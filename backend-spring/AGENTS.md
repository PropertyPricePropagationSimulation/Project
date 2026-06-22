# AGENTS.md

> 관련 문서: 기술 선택 근거는 `docs/DECISIONS.md` 참고. 스택 변경 전 반드시 읽을 것.

## Project Overview

부동산 정책 충격 전파 분석 시스템.
서울/경기 아파트 거래 데이터 기반 풍선효과(balloon effect) 및 연쇄 파급을 시각화한다.

- **Backend**: Spring Boot, Spring Batch (미사용 / 확장 예비), Spring Security, MyBatis, MySQL, DuckDB
- **Frontend**: Vue 3, Vite, Composition API (`<script setup>`), Vue Router, Pinia, axios, Mapbox GL JS
- **Infrastructure**: Docker, AWS
- **External**: AI 서버 (거래 raw 데이터 보유 + 분석 담당), 국토부 실거래가 API (예비), ECOS (예비), Kakao

---

## Data Flow

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

## Repository Structure

```
backend/
  src/main/java/com/example/home/
    batch/          # Spring Batch - 현재 미사용. 향후 확장 예비. 임의 삭제 금지.
      job/
        HouseDataCollectJob.java
        EcosDataCollectJob.java
      tasklet/
        HouseDataCollectTasklet.java
        EcosDataCollectTasklet.java
      scheduler/
        BatchScheduler.java
    analysis/       # AI 서버 연동, 응답 검증, 결과 저장 로직
    auth/           # JWT (access/refresh token), Spring Security 필터 체인
    house/          # 거래 데이터 도메인 (Entity, Service, Controller)
    scenario/       # 시나리오 탐색기 (G7) - 패턴 매칭 기반
  src/main/resources/
    mapper/         # MyBatis XML - SQL은 반드시 여기에만 작성
    application.properties # 환경별 설정 (local / dev / prod)

frontend/
  src/
    components/
      map/          # Mapbox GL JS 컴포넌트 (fill-extrusion, 레이어 조작)
    stores/         # Pinia store - 상태 관리만 담당
    api/            # axios 모듈 - 모든 API 호출은 여기서
    router/         # Vue Router 설정
    views/          # 페이지 단위 컴포넌트

scripts/
  verify-backend.sh
  verify-frontend.sh
  verify-analysis.sh
  verify-all.sh
  check-agent-risk.sh
  baseline/
    result_expected.json   # 분석 회귀 기준값

docs/
  DECISIONS.md

.claude/
  settings.json
```

---

## Coding Conventions

### Backend

- 모든 SQL은 `src/main/resources/mapper/` 의 MyBatis XML에 작성한다. Service 레이어 인라인 쿼리 금지.
- Spring Batch Job/Step 선언은 `batch/job/` 내부에서만 한다. 현재 미사용이지만 구조 임의 삭제 금지.
- **JWT 필터는 `@Component` 등록 금지.** 반드시 `SecurityConfig`의 `FilterRegistrationBean`으로만 등록한다. (이중 등록 버그 이력 있음. 절대 변경하지 말 것)
- `analysis/` 패키지는 AI 서버 연동, 요청/응답 DTO, 예외 처리, 결과 저장 로직만 담당한다.
- **에이전트는 풍선효과 지수, 시차 분석 등 AI 분석 알고리즘을 임의로 구현하지 않는다.** 정량 분석은 AI 서버가 담당한다.
- Controller는 요청/응답 변환만 담당한다. 비즈니스 로직 포함 금지.

### Spring Batch

- 배치 메타 테이블(`BATCH_JOB_INSTANCE`, `BATCH_JOB_EXECUTION` 등)은 MySQL에서 관리한다.
- DuckDB는 배치 실행 이력 저장소로 사용하지 않는다.
- 국토부/ECOS 수집이 필요해질 경우 `@Scheduled + Tasklet` 방식으로 구현한다.
- Chunk 방식은 대용량 스트리밍 또는 재시작 단위 제어가 필요할 때만 검토한다.

### DuckDB / MySQL 경계

- **DuckDB**: AI 서버에서 받은 거래 raw 데이터 저장 + 집계 쿼리 전용
- **MySQL**: 분석 결과 정형 데이터 저장 + API 서빙 전용
- 원본 거래 raw 데이터를 MySQL에 직접 적재하지 않는다.
- 분석 결과를 DuckDB에 저장하지 않는다.

### Frontend

- Vue 3 Composition API (`<script setup>`) 를 사용한다. Options API 혼용 금지.
- 지도 관련 로직(레이어 추가, fill-extrusion 조작, 애니메이션)은 `components/map/` 내부에서 완결한다.
- **fill-extrusion 레이어 조작은 Mapbox GL JS 네이티브 API만 사용한다. Three.js 혼용 금지.**
- API 호출은 `api/` 모듈에서만 담당한다. `stores/` 또는 컴포넌트에서 직접 axios 호출 금지.
- 페이지 단위 컴포넌트는 `views/`에, 공통 컴포넌트는 `components/`에 둔다.

### 공통

- 커밋 메시지: `feat / fix / refactor / docs / test` + 한글 설명
    - 예) `feat: 풍선효과 지수 시차 계산 로직 추가`
- 환경변수, API 키는 코드에 하드코딩 금지. `application.properties` 또는 환경변수로 관리.

---

## What Agents Should / Should Not Do

### 자율적으로 해도 되는 것

- `analysis/` 패키지 내 AI 연동 로직 추가·수정
- `mapper/` XML에 쿼리 추가
- Vue 컴포넌트 신규 생성 및 수정
- 기존 패턴을 따르는 단위 테스트 작성
- JavaDoc, 주석 추가
- `docs/` 내 문서 수정

### 반드시 사람이 판단할 것

- Spring Security 필터 체인 변경
- DB 스키마 변경 (DDL, migration 포함)
- Spring Batch Job 구조 변경
- 외부 API 연동 추가 또는 변경 (AI 서버, 국토부, ECOS, Kakao)
- `application.properties` 또는 환경변수 수정
- 의존성 추가/변경 (`pom.xml`, `package.json`)
- 인증/인가 로직 변경
- DuckDB ↔ MySQL 저장 경계 변경

위 항목이 필요하다고 판단되면 **직접 수정하지 말고 변경 제안과 이유를 작성**한다.

---

## Build & Test

```bash
# Backend 실행
cd backend && ./mvnw spring-boot:run -Dspring-boot.run.profiles=local

# Frontend 실행
cd frontend && npm run dev

# Backend 테스트
cd backend && ./mvnw test

# 전체 검증
bash scripts/verify-all.sh

# 분석 연동 테스트 (analysis/ 수정 시 필수)
bash scripts/verify-analysis.sh

# 위험 파일 변경 여부 확인
bash scripts/check-agent-risk.sh
```

- 통합 테스트는 `@SpringBootTest` 어노테이션이 붙은 것만 해당하며, H2 in-memory DB를 사용한다.
- `analysis/` 로직 수정 시에는 `verify-analysis.sh`를 반드시 실행하고 결과를 보고에 포함한다.

---

## Completion Criteria

작업 완료 전 반드시 아래 형식으로 보고한다.

```
### 작업 완료 보고

**변경 파일 목록**
- (변경된 파일 경로 및 변경 요약)

**실행한 검증**
- [ ] ./mvnw test 통과 여부
- [ ] npm run build 통과 여부 (frontend 변경 시)
- [ ] verify-analysis.sh 실행 결과 (analysis/ 변경 시)

**실행하지 못한 검증**
- (이유와 함께 명시)

**사람 판단이 필요한 사항**
- (해당 없으면 "없음")
```

DB 스키마, 인증, 배치 구조, 환경변수 변경이 필요한 경우 직접 수정하지 말고 이 섹션에 제안만 작성한다.