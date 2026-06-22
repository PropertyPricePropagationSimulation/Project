# DECISIONS.md

기술 선택 근거 및 설계 결정 사항. 스택 변경 전 반드시 확인할 것.

---

## 데이터 흐름

```
AI 서버 (거래 raw 데이터 보유)
    ↓ raw 데이터 전달
DuckDB (raw 데이터 저장 + 집계 쿼리)
    ↓ 집계/분석 결과
Spring Boot (결과 가공, API 서빙)
    ↓ 분석 결과 저장
MySQL (정형 결과 저장)
    ↓
Vue.js (Mapbox 시각화)
```

---

## DuckDB + MySQL 병용

- **DuckDB**: AI 서버에서 받은 거래 raw 데이터 저장 + Parquet 기반 집계 쿼리 전용
- **MySQL**: 분석 결과 정형 데이터 저장 + Spring Boot API 서빙 전용
- 원본 거래 raw 데이터를 MySQL에 직접 적재하지 않는다. (대용량 비정형 데이터 → MySQL 부적합)
- 분석 결과를 DuckDB에 저장하지 않는다. (API 서빙 연결 관리 복잡도 증가)
- Spring Batch 메타 테이블(`BATCH_JOB_INSTANCE` 등)은 MySQL에서 관리한다.

## Mapbox GL JS

- fill-extrusion 기반 3D 시각화 필요
- Kakao Map은 3D extrusion 표현이 제한적 → 대체 불가
- Three.js는 Mapbox와 혼용 시 레이어 충돌 이력 있음 → 혼용 금지

## MyBatis

- 복잡한 지역별 집계 쿼리 직접 제어 필요
- JPA 자동 쿼리로는 성능 불확실
- SQL은 `src/main/resources/mapper/` XML에서만 관리

## Vue 3 + Vite + Composition API

- Vue 3 Composition API (`<script setup>`) 사용
- Vite 기반 빌드 (Vue CLI 대체)
- Options API 혼용 금지 (코드 일관성)

## AI 분석 범위

- 정책 충격 분석(풍선효과 지수, 시차 분석 등)은 AI 서버가 담당한다.
- Spring Boot 백엔드는 AI 서버 호출, 응답 검증, 결과 저장, 조회 API만 담당한다.
- 백엔드에서 분석 알고리즘을 임의로 구현하지 않는다.

## Spring Batch

- 현재 미사용. 향후 자체 데이터 수집 또는 AI 서버 결과 동기화 용도로 확장 가능.
- 국토부/ECOS 수집이 필요해질 경우 `@Scheduled + Tasklet` 방식으로 구현한다.
- Chunk 방식은 대용량 스트리밍 또는 재시작 단위 제어가 필요할 때만 검토한다.
- Job/Step 구조는 유지하되 실제 스케줄 실행은 비활성 상태.