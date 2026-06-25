# EstateFlow

> 부동산 정책 충격 전파 분석 시스템

[![Vue](https://img.shields.io/badge/Vue.js-3.x-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-4.x-6DB33F?logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.x-FFC107?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

---

## 소개

국토교통부 실거래가 공공 API로 수집한 아파트 매매 실거래 데이터를 기반으로, 기준금리 변동·부동산 정책 이벤트 이후 서울 25개구 및 수도권 거점 지역의 가격·거래량 충격이 어떤 순서와 강도로 전파되었는지 분석·시각화하는 시스템입니다.
지도 히트맵과 타임라인 슬라이더로 충격 전파 흐름을 탐색하고, AI가 분석 결과를 자동 리포트로 요약합니다. 분석 수치를 기반으로 시장 참여자(투자자·실수요자·임차인·중개사) 페르소나의 라운드별 반응 흐름을 시나리오 형태로 탐색할 수 있습니다.

---

## 화면 미리보기

| 메인 분석 화면 | 지도 히트맵 |
|:---:|:---:|
| ![메인 분석](docs/image/screenshots/analysis.png) | ![지도 히트맵](docs/image/screenshots/map.png) |

| 시나리오 탐색기 | AI 리포트 |
|:---:|:---:|
| ![시나리오](docs/image/screenshots/scenario.png) | ![리포트](docs/image/screenshots/report.png) |

| 공지사항 | 로그인 / 마이페이지 |
|:---:|:---:|
| ![공지사항](docs/image/screenshots/notice.png) | ![로그인](docs/image/screenshots/login.png) |

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 실거래가 ETL 파이프라인 | 국토부 MOLIT API 수집 → 취소 거래·이상치 제거 → Parquet 저장 → DuckDB 등록 |
| 이벤트 관리 | 기준금리(ECOS) 자동 수집 및 정책 이벤트 관리자 등록. 분석 window(3·6·12개월) 설정 |
| 충격 전파 분석 | 이벤트월 기준 지역별 가격 변화율·거래량 변화율·반응 시차(lag)·충격 강도 점수 산출 |
| 지도 시각화 | Mapbox GL 기반 지역별 변화율 히트맵, 타임라인 슬라이더, TOP 5 선·후행 지역 표시 |
| AI 분석 리포트 | Spring AI + OpenAI 기반 분석 결과 자동 요약 및 PDF 리포트 생성 |
| 시나리오 탐색기 | 분석 수치를 규칙 기반으로 에이전트 state에 반영 → LLM이 투자자·실수요자·갈아타기 수요층 페르소나 언어로 라운드별 서술 |
| 실거래 검색 | 지역·연월 기준 아파트 매매 실거래 목록 조회 |
| 회원 / Q&A | JWT 인증 (access + refresh token 자동 갱신), 공지사항, Q&A 게시판 |

---

## 기술 스택

### Frontend

| 분류 | 기술 |
|------|------|
| Framework | Vue 3 |
| Build | Vite |
| Language | TypeScript |
| Routing | Vue Router 5 |
| 상태 관리 | Pinia |
| HTTP | Axios |
| 지도 | Mapbox GL |
| 온보딩 투어 | driver.js |
| 코드 품질 | ESLint + OxLint + Prettier |

### Backend (Spring)

| 분류 | 기술 |
|------|------|
| Framework | Spring Boot 4.x |
| DB 접근 | MyBatis |
| 인증/인가 | Spring Security + JWT |
| AI | Spring AI — OpenAI 호환 API (리포트 생성, 시나리오 서술) |
| 캐시 | Redis |
| PDF 생성 | Thymeleaf + OpenHTMLtoPDF |
| API 문서 | SpringDoc OpenAPI (Swagger UI) |
| XML 파싱 | Jackson Dataformat XML (국토부 API) |

### Backend (FastAPI)

| 분류 | 기술 |
|------|------|
| Framework | FastAPI + uvicorn |
| 분석 DB | DuckDB |
| 데이터 처리 | pandas, numpy |
| HTTP 클라이언트 | httpx |
| 설정 | python-dotenv |

### 외부 API

| API | 용도 |
|-----|------|
| 국토교통부 실거래가 API (MOLIT) | 아파트 매매 실거래 데이터 수집 |
| 한국은행 ECOS Open API | 기준금리 등 경제지표 수집 |
| R-ONE 부동산통계정보시스템 API | 지역별 매매가격지수 보조 지표 |
| 행정안전부 법정동코드 API | 지역코드 매핑 |

### Infrastructure

| 분류 | 기술 |
|------|------|
| DB | MySQL 8 (회원·이벤트·리포트), DuckDB (실거래 분석) |
| 캐시 | Redis 7 |
| 컨테이너 | Docker + Docker Compose (Redis) |
| 데이터 형식 | Parquet (원본·정제 실거래가), DuckDB 파일 |

---

## 시스템 아키텍처

![System Architecture](docs/image/SYSTEM_ARCHITECTURE.png)

---

## 프로젝트 구조

```
EstateFlow/
├── frontend/                        # Vue 3 + Vite SPA
│   └── src/
│       ├── views/                   # 라우트별 페이지 (Analysis, Scenario, Report, Home 등)
│       ├── components/              # 공통 · 도메인 컴포넌트 (지도, 분석 패널 등)
│       ├── stores/                  # Pinia 스토어 (auth, analysis, scenario, report)
│       ├── api/                     # Axios 기반 API 클라이언트
│       ├── types/                   # TypeScript 타입 정의
│       └── router/                  # Vue Router 설정
│
├── backend-spring/                  # Spring Boot REST API
│   ├── docker-compose.yml           # Redis 실행 구성
│   ├── scripts/sql/schema.sql       # MySQL 스키마
│   └── backend/src/main/java/…/
│       └── domain/
│           ├── auth/                # JWT 인증
│           ├── member/              # 회원 관리
│           ├── house/               # 국토부 실거래 조회
│           ├── analysis/            # FastAPI 분석 결과 중계 · 캐시
│           ├── report/              # AI 리포트 생성 · PDF 출력
│           ├── scenario/            # AI 시나리오 탐색기
│           ├── notice/              # 공지사항
│           └── qna/                 # Q&A 게시판
│
└── backend-fastAPI/                 # Python 분석 서버
    └── app/
        ├── api/                     # 라우터 (analysis, event, batch, collect, preprocess)
        ├── services/                # 비즈니스 로직 (collector, etl, duckdb_service, analysis)
        ├── schemas.py               # Pydantic 스키마
        ├── config.py                # 설정
        └── main.py                  # FastAPI 앱 진입점
```

---

## 로컬 개발 환경 설정

### 사전 요구사항

- Java 21+
- Node.js 22+ (또는 24+)
- Python 3.12+
- Docker + Docker Compose
- MySQL 8

### 1. Redis 실행 (공통)

```bash
cd backend-spring
docker compose up -d
```

### 2. MySQL 스키마 초기화

```bash
mysql -u root -p < backend-spring/scripts/sql/schema.sql
```

### 3. Spring 백엔드

```bash
cd backend-spring/backend

# .env 파일 직접 생성 후 아래 환경 변수 섹션을 참고하여 값 입력
# (backend-spring/backend/.env)

# 마이그레이션 실행 (schema.sql 이후 순서대로 적용)
mysql -u root -p estateflow < scripts/sql/migrations/001_add_birth_date.sql
mysql -u root -p estateflow < scripts/sql/migrations/002_add_analysis_cache.sql
mysql -u root -p estateflow < scripts/sql/migrations/003_add_report_history.sql
mysql -u root -p estateflow < scripts/sql/migrations/004_add_report_history_deleted_at.sql

# 실행
./mvnw spring-boot:run
```

### 4. FastAPI 분석 서버

```bash
cd backend-fastAPI

# 가상환경 생성 및 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt

# 환경 변수 설정
# .env 파일 생성 후 아래 환경 변수 섹션 참고

# 서버 실행
uvicorn app.main:app --reload
```

> **DuckDB 데이터 준비**: `backend-fastAPI/result/ssafy.duckdb` 파일이 있으면 MOLIT 데이터를 새로 수집할 필요 없이 바로 분석 API를 사용할 수 있습니다.

### 5. 프론트엔드

```bash
cd frontend

pnpm install

# 환경 변수 설정
# .env.local 파일 생성 후 아래 환경 변수 섹션 참고 .env.local 파일 생성 후 아래 환경 변수 섹션 참고

# 개발 서버 실행 (http://localhost:5173)
pnpm run dev
```

---

## 환경 변수

### Spring (`backend-spring/backend/.env`)

| 변수 | 설명 |
|------|------|
| `DB_URL` | MySQL 접속 URL (예: `jdbc:mysql://localhost:3306/estateflow?...`) |
| `DB_USERNAME` / `DB_PASSWORD` | MySQL 접속 정보 |
| `REDIS_HOST` / `REDIS_PORT` | Redis 접속 정보 |
| `JWT_SECRET_KEY` | JWT 서명 키 (32자 이상) |
| `JWT_ACCESS_EXPIRE_SECONDS` | Access token 만료 시간 (기본: `1800`) |
| `JWT_REFRESH_EXPIRE_SECONDS` | Refresh token 만료 시간 (기본: `604800`) |
| `OPENAI_API_KEY` | OpenAI 호환 API 키 |
| `OPENAI_MODEL` | 사용 모델 (기본: `gpt-4o-mini`) |
| `OPENAI_BASE_URL` | OpenAI 호환 API base URL |
| `OPENAI_CHAT_COMPLETIONS_PATH` | Chat completions 경로 (기본: `chat/completions`) |
| `AI_SERVER_URL` | FastAPI 분석 서버 주소 (기본: `http://localhost:8000`) |
| `molit.api.service-key` | 국토부 실거래가 API 서비스 키 |

### 프론트엔드 (`frontend/.env.local`)

| 변수 | 설명 |
|------|------|
| `VITE_MAPBOX_TOKEN` | Mapbox GL 퍼블릭 액세스 토큰 |

### FastAPI (`backend-fastAPI/.env`)

| 변수 | 설명 |
|------|------|
| `MOLIT_API_KEY` | 국토부 실거래가 API 키 |
| `ECOS_API_KEY` | 한국은행 ECOS API 키 |
| `JUSO_API_KEY` | 행안부 법정동코드 API 키 |
| `RONE_API_URL` | R-ONE API URL |
| `RONE_API_KEY` | R-ONE API 키 |

---

## API 문서

로컬 실행 후 아래 URL에서 Swagger UI를 확인할 수 있습니다.

```
# Spring 백엔드
http://localhost:8080/swagger-ui.html

# FastAPI 분석 서버
http://localhost:8000/docs
```

### Spring 주요 엔드포인트 (프론트엔드 연동)

프론트엔드는 Spring 백엔드(`/api/*`)만 직접 호출합니다. FastAPI는 Spring이 내부적으로 중계 호출합니다.

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/analysis/events` | 이벤트 목록 조회 |
| `POST` | `/api/analysis/event-window` | 이벤트 기반 지역별 충격 분석 |
| `POST` | `/api/reports` | AI 리포트 생성 |
| `GET` | `/api/reports/my` | 내 리포트 목록 조회 |
| `GET` | `/api/reports/{reportId}/pdf` | 리포트 PDF 다운로드 |
| `POST` | `/api/scenarios` | 시나리오 생성 |
| `POST` | `/api/scenarios/{id}/rounds/{month}/explanation` | 라운드별 AI 서술 생성 |

### FastAPI 주요 엔드포인트 (Spring → FastAPI 내부 연동)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/events/json` | 이벤트 목록 (Spring이 조회) |
| `POST` | `/analysis/event-window` | 이벤트 기반 지역별 충격 분석 |
| `POST` | `/api/batch/import/sale-data` | MOLIT 실거래 데이터 수집 배치 |
| `POST` | `/api/batch/register-parquet-files` | Parquet → DuckDB 등록 |
| `GET` | `/api/batch/status` | 데이터 적재 상태 확인 |

---

## 분석 개념

| 개념 | 정의 |
|------|------|
| **반응 시차 (Lag)** | 이벤트 발생 후 해당 지역이 임계 변화율을 처음 초과한 시점까지의 차이 |
| **충격 전파 (Diffusion)** | 선행 반응 지역에서 후행 반응 지역으로 가격·거래량 변화가 확산되는 경로 |
| **풍선효과 (Displacement)** | 규제 지역 거래 감소 → 인접·외곽 지역 거래 증가로 수요가 이동하는 패턴 |
| **충격 강도 점수** | 가격 변화율(60%) + 거래량 변화율(40%) 가중 합산 점수 |
| **페르소나** | 투자자(`INVESTOR`), 실수요자(`END_USER`), 갈아타기 수요층(`MOVER`) |

> 본 시스템은 미래 가격 예측이 아닌 **과거 반응 패턴 탐색**을 목적으로 합니다. 지역 간 전파 구조는 시차 및 변화율 상관 구조 기반 추정이며, 인과관계가 아닌 상관관계임을 명시합니다.

---

## 관련 문서

- [기획서](backend-fastAPI/기획서%20수정%200515요약.md)
- [아키텍처 결정 기록](backend-spring/docs/DECISIONS.md)
