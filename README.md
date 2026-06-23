# FastAPI 부동산 데이터 분석 백엔드

SSAFY Home 프로젝트의 FastAPI 기반 부동산 실거래가 분석 백엔드입니다.

이 백엔드는 공공 API에서 수집한 아파트 매매 실거래 데이터를 정제해 DuckDB에 적재하고, 정책/경제 이벤트를 기준으로 Spring 백엔드가 분석에 사용할 수 있는 JSON 데이터를 제공합니다.

## 개요

구성:

- **ETL 파이프라인**: MOLIT 실거래가 API 원본 수집 후 Parquet 저장
- **경제지표 수집**: ECOS 기준금리 등 거시지표 수집 및 전처리
- **DuckDB 분석**: 월별 지역 집계 데이터와 이벤트 테이블 기반 분석
- **REST API**: 이벤트 조회, 이벤트 기준 분석, 집계 데이터 조회, 배치 작업

대상 지역:

- 프로젝트 기준 서울 25개구 + 수도권 거점 9개시
- MOLIT 수집 시 일부 경기 지역은 상위 시 코드가 데이터를 반환하지 않아 하위 행정 코드로 나누어 총 49개 LAWD_CD를 수집합니다.

분석 기간:

- 현재 보유 월별 요약 데이터 범위는 DuckDB의 `house_monthly_summary` 기준입니다.
- 기준금리 이벤트는 `processed/ecos/base_rate_changes_200501_202512.csv` 기준 47건을 적재했습니다.

## 현재 구현 상태

### G1. 데이터 수집(관리자 작업)

- MOLIT 실거래가 API 원본 응답을 `raw/`에 저장합니다.
- ECOS 기준금리 등 경제지표 원본 데이터를 수집할 수 있습니다.
- 수집 원본은 `.meta.json`과 함께 저장해 호출 조건을 추적합니다.
- API 키는 메타데이터에 저장될 때 마스킹합니다.


### G2. 전처리 및 DuckDB 등록(관리자 작업)

- 원본 실거래 데이터를 정제해 `processed/` 아래 Parquet 파일로 저장합니다.
- 취소 거래와 이상치를 제외한 뒤 월별 지역 요약 데이터를 생성합니다.
- 월별 지역 집계 데이터는 `processed/monthly_summary/house_monthly_summary.parquet`로 생성됩니다.
- DuckDB의 `house_monthly_summary` 테이블로 등록해 분석 API에서 조회합니다.

주요 테이블:

```text
house_monthly_summary
- dong_code
- deal_year
- deal_month
- deal_count
- avg_deal_amount
- median_deal_amount
- avg_price_per_sqm
- min_price_per_sqm
- max_price_per_sqm
- is_low_volume
- year_month
```

### G3. 이벤트 관리(관리자가 미리 등록 후 꺼내서 사용)

G3는 완료 상태로 봅니다.

이벤트를 공통 테이블과 세부 테이블로 분리했습니다. 현재는 기준금리 이벤트를 다루지만, 이후 부동산 정책 발표일, 규제지역 지정, 공급 정책 같은 이벤트도 같은 구조로 확장할 수 있습니다.

설계 원칙:

- `events`는 모든 이벤트의 공통 메타데이터를 담습니다.
- 이벤트 유형별 세부 정보는 별도 테이블에 저장합니다.
- 분석 window는 이벤트의 고정 속성이 아니므로 DB에 저장하지 않습니다.
- window는 Spring/FastAPI 분석 요청 JSON으로 전달하는 파라미터로 처리합니다.

DuckDB 이벤트 테이블:

```text
events
- id
- name
- event_type
- event_date
- event_ym
- source
- description
```

```text
base_rate_event_details
- event_id
- previous_rate
- new_rate
- delta
- direction
- previous_observed_date
- stat_code
- item_code
- item_name
```

```text
policy_event_details
- event_id
- policy_category
- policy_direction
- target_region
- affected_asset
- announced_date
- effective_date
- source_url
```

기준금리 이벤트 적재 상태:

```text
events: 47건
base_rate_event_details: 47건
policy_event_details: 0건
```

재실행 가능한 적재 스크립트:

```bash
python scripts/import_base_rate_events.py
```

Windows 환경에서 직접 실행이 막히는 경우:

```bash
.venv\Scripts\python.exe -c "from scripts.import_base_rate_events import main; main()"
```

스크립트는 중복 적재를 방지합니다.

```text
Imported 0 base-rate events.
Skipped 47 existing events.
```

Spring 전달용 이벤트 JSON API:

```http
GET /events/json
GET /events/json?include_details=false
```

응답 예시:

```json
{
  "status": "success",
  "count": 47,
  "events": [
    {
      "id": 47,
      "name": "한국은행 기준금리 인하 2.75% -> 2.5%",
      "event_type": "base_rate",
      "event_date": "2025-05-29",
      "event_ym": "202505",
      "source": "ECOS",
      "description": "한국은행 기준금리 2.75%에서 2.5%로 -0.25%p 인하",
      "detail": {
        "previous_rate": 2.75,
        "new_rate": 2.5,
        "delta": -0.25,
        "direction": "cut",
        "previous_observed_date": "2025-05-28",
        "stat_code": "722Y001",
        "item_code": "0101000",
        "item_name": "한국은행 기준금리"
      }
    }
  ]
}
```

관련 파일:

```text
app/api/event.py
app/services/event_service.py
app/services/duckdb_service.py
app/schemas.py
scripts/import_base_rate_events.py
```

### G4. 이벤트 기반 분석(사용자 입력 받음)

G4 이벤트월 기준 변화율 분석 API를 추가했습니다.

Spring이 선택한 이벤트와 window 조건을 FastAPI 분석 API로 넘기면, FastAPI는 DuckDB의 `house_monthly_summary`와 이벤트 테이블을 기준으로 이벤트 발생 월을 기준점으로 잡고 전후 월별 가격 변화율, 거래량 변화율, 반응 시점, 충격 강도 점수를 계산합니다.

현재 window는 3개월, 6개월, 12개월 중 하나만 선택할 수 있습니다. 월별 집계 데이터를 사용하므로 이벤트 발생 월(`event_ym`)을 기준값 0%로 두고, `-n개월 ~ +n개월` 범위의 변화를 계산합니다.

#### G4 지표 기준

G4의 메인 가격 지표는 `avg_price_per_sqm`입니다. 따라서 응답의 `price_change_from_event_pct`, `final_price_change_pct`, `top_price_rise`, `top_price_drop`, `reaction_ym`, `impact_score`는 모두 이벤트월의 면적당 평균가격 대비 변화율을 기준으로 계산합니다.

`avg_deal_amount`는 거래된 주택의 면적 구성에 크게 흔들릴 수 있으므로 메인 가격 지표로 사용하지 않습니다. 대신 참고용 보조 지표인 `deal_amount_change_from_event_pct`, `final_deal_amount_change_pct`로 함께 제공합니다.

예를 들어 `final_price_change_pct = -10.83`, `final_deal_amount_change_pct = 5.41`이면, 이벤트월 대비 window 마지막 월의 면적당 평균가격은 10.83% 하락했지만 평균 거래금액은 5.41% 상승했다는 뜻입니다. 이는 더 큰 면적의 주택이 많이 거래되면 실제로 가능한 조합입니다.

분석 API:

```http
POST /analysis/event-window
```

요청 예시:

```json
{
  "event_id": 30,
  "window_months": 3,
  "region_codes": null
}
```

`region_codes`는 선택값입니다. `null`이거나 생략하면 전체 지역을 분석하고, 특정 지역만 보고 싶을 때만 `["11650", "11680"]`처럼 전달합니다.

응답 구조:

```text
event       이벤트 정보
analysis    분석 모드, 기준월, 분석 기간, 임계값
summary     전체 지역 요약
rankings    상승/하락/거래량/반응속도/충격강도 TOP
regions     지역별 baseline, 요약, 월별 변화율
```

응답 예시:

```json
{
  "status": "success",
  "event": {
    "id": 30,
    "event_date": "2019-07-18",
    "event_ym": "201907"
  },
  "analysis": {
    "mode": "event_month_indexed",
    "window_months": 3,
    "baseline_ym": "201907",
    "period": {
      "start_ym": "201904",
      "end_ym": "201910"
    },
    "threshold_pct": 5.0
  },
  "summary": {
    "region_count": 3,
    "complete_window_count": 3,
    "avg_price_change_after_window_pct": 3.19,
    "avg_volume_change_after_window_pct": 8.91,
    "rising_region_count": 3,
    "falling_region_count": 0,
    "strong_reaction_region_count": 1
  },
  "rankings": {
    "top_price_rise": [],
    "top_price_drop": [],
    "top_volume_rise": [],
    "fastest_reaction": [],
    "highest_impact": []
  },
  "regions": [
    {
      "dong_code": "11650",
      "baseline": {
        "year_month": "201907",
        "avg_deal_amount": 161391.58,
        "median_deal_amount": 150000.0,
        "avg_price_per_sqm": 1716.49,
        "deal_count": 493
      },
      "window_summary": {
        "final_price_change_pct": 3.1,
        "final_deal_amount_change_pct": 3.1,
        "final_volume_change_pct": -3.85,
        "max_price_rise_pct": 9.05,
        "max_price_drop_pct": 3.1,
        "reaction_ym": "201908",
        "lag_months": 1,
        "direction": "rise",
        "impact_score": 3.4,
        "is_complete_window": true
      },
      "monthly": [
        {
          "year_month": "201904",
          "relative_month": -3,
          "avg_deal_amount": 153450.48,
          "deal_count": 124,
          "price_change_from_event_pct": -4.92,
          "deal_amount_change_from_event_pct": -15.86,
          "volume_change_from_event_pct": -74.85
        },
        {
          "year_month": "201907",
          "relative_month": 0,
          "avg_deal_amount": 161391.58,
          "deal_count": 493,
          "price_change_from_event_pct": 0.0,
          "deal_amount_change_from_event_pct": 0.0,
          "volume_change_from_event_pct": 0.0
        }
      ]
    }
  ]
}
```

## 빠른 시작

### 1. 가상환경 및 의존성 설치

```bash
cd backend-fastAPI
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Mac/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 직접 생성합니다.

```text
JUSO_API_KEY=your_key
MOLIT_API_KEY=your_key
ECOS_API_KEY=your_key
RONE_API_URL=your_rone_api_url
RONE_API_KEY=your_key
```

### 3. FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

프로덕션 예시:

```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## 데이터 준비 여부

이미 `result/ssafy.duckdb` 파일이 있고, 그 안에 아래 테이블이 존재한다면 G4 분석 API를 실행하기 위해 MOLIT/ECOS 데이터를 새로 수집할 필요는 없습니다.

```text
house_monthly_summary
events
base_rate_event_details
policy_event_details
```

이 상태에서는 Spring 또는 Swagger에서 바로 아래 API를 호출해 이벤트 목록과 분석 결과를 JSON으로 받을 수 있습니다.

```http
GET /events/json
POST /analysis/event-window
```

새 데이터 수집 또는 재전처리가 필요한 경우는 다음과 같습니다.

- 분석 기간을 더 최신 월까지 확장해야 하는 경우
- `house_monthly_summary`가 비어 있거나 누락된 경우
- 기준금리 또는 정책 이벤트 데이터를 새로 갱신해야 하는 경우
- 원본 수집/전처리/이상치 제거 로직을 바꿔 기존 DuckDB를 다시 생성해야 하는 경우

## 주요 API

### Spring 과의 연동에 사용되는 API

이벤트 목록 요청
```http
GET /events/json
GET /events/json?include_details=false
```

분석
```http
POST /analysis/event-window
```


### 이벤트 API(GET/event/json을 주로 사용할 예정 - 이벤트 목록 전달의 목적)

```http
GET /events/
GET /events/json
POST /events/
PUT /events/{event_id}
DELETE /events/{event_id}
```

### 분석 API(POST/analysis/event-window를 주로 사용할 예정 - 사용자가 이벤트 종류, 관찰 기간, 보고 싶은 지역(선택 X -> 전지역 대상) 선택 시 분석 결과 JSON으로 줌)

```http
POST /analysis/event-window
GET /analysis/search/houses
GET /analysis/stats/by-region
GET /analysis/stats/by-year
```

### 배치 API(관리자가 데이터를 수집할 때 사용)

```http
POST /api/batch/import/sale-data?start_ym=200501&end_ym=202512
POST /api/batch/register-parquet-files
GET /api/batch/status
GET /api/batch/import/sale-data/regions
```

### 원본 데이터 수집 API(이벤트에 해당하는 기준금리 등의 데이터 수집을 목적으로 사용)

```http
POST /collect/ecos/raw
POST /collect/r-one/raw
```

## 배치 및 수집 사용법(이미 끝냈음 시간이 오래걸리기 때문에 하지 않는 것을 추천함)

### 테스트 수집

```bash
python scripts/test_collection.py
```

### 전체 수집

```bash
python scripts/run_full_etl.py
```

전체 수집은 지역과 기간이 넓으면 오래 걸릴 수 있습니다. 공공 API 호출 제한이 있으므로 연월과 지역 범위를 나누어 실행하는 것을 권장합니다.

### MOLIT 실거래가 수집

```http
POST /api/batch/import/sale-data?start_ym=200501&end_ym=202512
```

주요 쿼리 파라미터:

- `start_ym`: 수집 시작 연월, `YYYYMM` 형식
- `end_ym`: 수집 종료 연월, `YYYYMM` 형식
- `region_codes`: 직접 지정할 LAWD_CD 목록. 미지정 시 `app.config_regions.get_region_codes()` 사용
- `max_regions`: 한 번에 처리할 최대 지역 수. 기본값 49

### Parquet 파일을 DuckDB에 등록

```http
POST /api/batch/register-parquet-files
```

전처리로 생성된 `processed/monthly_summary/house_monthly_summary.parquet`을 DuckDB의 `house_monthly_summary` 테이블로 로드합니다.

### 등록된 데이터 상태 확인

```http
GET /api/batch/status
```

### ECOS 원본 저장

```http
POST /collect/ecos/raw
```

요청 예시:

```json
{
  "stat_code": "722Y001",
  "cycle": "M",
  "start_time": "202001",
  "end_time": "202512",
  "item_code1": "0101000",
  "output_format": "json"
}
```

저장 예시:

```text
raw/ecos_722Y001_M_202001_202512_YYYYMMDDHHMMSSffffff.json
raw/ecos_722Y001_M_202001_202512_YYYYMMDDHHMMSSffffff.json.meta.json
```

### R-ONE 원본 저장

```http
POST /collect/r-one/raw
```

`RONE_API_URL`에 설정된 API로 GET 요청을 보내고 응답 원문을 `raw/`에 저장합니다. API마다 파라미터 형식이 다를 수 있으므로 요청 body의 `params`에 필요한 쿼리 파라미터를 그대로 전달합니다.

요청 예시:

```json
{
  "params": {
    "regionCd": "11680",
    "startYm": "202001",
    "endYm": "202512"
  }
}
```

## 데이터 경로(용량 문제로 정제된 데이터를 저장하고 있는 result폴더만 업로드 함 - 필요 시 요청할 것)

```text
raw/
  공공 API 원본 응답

processed/
  정제된 Parquet 및 ECOS 전처리 CSV

processed/ecos/
  base_rate_changes_200501_202512.csv
  monthly_macro_indicators_200501_202512.csv

processed/monthly_summary/
  house_monthly_summary.parquet

result/
  ssafy.duckdb
```

MOLIT 원본 저장 예시:

```text
raw/sale_data_{LAWD_CD}_{YYYYMM}_p{page}_{YYYYMMDDHHMMSSffffff}.xml
raw/sale_data_{LAWD_CD}_{YYYYMM}_p{page}_{YYYYMMDDHHMMSSffffff}.xml.meta.json
```

정제 거래 데이터 저장 위치:

```text
processed/{year}/{month}/houses_{dong_code}.parquet
```

월별 지역 요약 데이터 저장 위치:

```text
processed/monthly_summary/house_monthly_summary.parquet
```

처리 이력:

```text
processed/manifest.json
```

## 데이터 구조

### 정제 거래 데이터 주요 컬럼

| 컬럼 | 의미 |
| --- | --- |
| `apt_name` | 아파트 또는 건물명 |
| `sido_name` | 시도명 |
| `gugun_name` | 시군구명 |
| `dong_name` | 법정동명 |
| `dong_code` | 수집 요청에 사용된 LAWD_CD 지역 코드 |
| `jibun` | 지번 |
| `road_name` | 도로명 |
| `build_year` | 건축 연도 |
| `floor` | 거래 층 |
| `deal_year` | 거래 연도 |
| `deal_month` | 거래 월 |
| `deal_day` | 거래 일 |
| `contract_date` | 거래 연월일이 모두 확인된 경우의 계약일 |
| `estimated_contract_date` | 분석용 계약일 추정값. 현재는 `contract_date`와 동일 |
| `date_uncertainty_days` | 날짜 불확실성 일수 |
| `deal_amount` | 거래금액. 단위는 공공데이터 원문 기준의 만원 |
| `exclu_use_ar` | 전용면적 |
| `price_per_sqm` | `deal_amount / exclu_use_ar`로 계산한 면적당 거래금액 |
| `deal_type` | 거래 유형 |
| `cancel_type` | 해제 또는 취소 유형 |
| `cancel_date` | 해제 또는 취소일 |
| `is_cancelled` | 취소 거래 여부 |
| `is_direct_trade` | 직거래 여부 |
| `is_special_trade` | 특수 거래 여부 |
| `is_outlier` | 이상치 여부 |
| `source_raw_file` | 전처리에 사용된 원본 raw XML 파일명 |
| `preprocessed_at` | 전처리 실행 시각 |

전처리 과정에서는 취소 거래를 제거하고, 비교 가능한 거래가 충분한 월/지역 그룹에서는 면적당 거래금액 기준 이상치를 표시한 뒤 정제 데이터 저장 시 이상치를 제외합니다.

### 월별 지역 요약 데이터

| 컬럼 | 의미 |
| --- | --- |
| `dong_code` | 지역 코드 |
| `deal_year` | 거래 연도 |
| `deal_month` | 거래 월 |
| `deal_count` | 해당 월/지역의 거래 건수 |
| `avg_deal_amount` | 평균 거래금액 |
| `median_deal_amount` | 중앙값 거래금액 |
| `avg_price_per_sqm` | 평균 면적당 거래금액 |
| `min_price_per_sqm` | 최소 면적당 거래금액 |
| `max_price_per_sqm` | 최대 면적당 거래금액 |
| `is_low_volume` | 거래 건수가 `min_deal_count`보다 작은 저표본 여부 |
| `year_month` | `YYYYMM` 형식의 연월 |
| `created_at` | 요약 데이터 생성 시각 |

## DuckDB 확인 예시

```bash
.venv\Scripts\python.exe -c "import duckdb; con=duckdb.connect('result/ssafy.duckdb'); print(con.execute('show tables').fetchall())"
```

현재 기대 테이블:

```text
base_rate_event_details
events
house_monthly_summary
policy_event_details
```

## 주요 서비스 모듈

### `app.services.collector`

- `collect_legal_dong_code()`: JUSO API에서 법정동 코드 조회
- `collect_sale_data()`: MOLIT API에서 거래 데이터 수집 및 ETL

### `app.services.etl`

- `write_parquet_from_df()`: DataFrame을 Parquet으로 저장
- `update_manifest()`: 처리 이력 추적
- `run_initial_load()`: 전체 ETL 오케스트레이션

### `app.services.duckdb_service`

- `get_connection()`: DuckDB 연결
- `init_schema()`: DuckDB의 애플리케이션 테이블 초기화
- `register_parquet_files()`: 월별 지역 요약 Parquet을 `house_monthly_summary` 테이블로 로드
- `list_tables()`: DuckDB 테이블 목록 조회

### `app.config_regions`

- `get_region_codes()`: MOLIT 수집 대상 49개 LAWD_CD 반환
- `get_project_region_groups()`: 프로젝트 지역 코드와 실제 수집 LAWD_CD 목록의 매핑 반환

## G1-G4 실행 모델

### G1-G2: 개발자/운영자용 배치 파이프라인

G1과 G2는 일반 사용자가 매번 실행하는 기능이라기보다, 서비스 전에 개발자 또는 운영자가 먼저 수행하는 ETL 작업으로 봅니다.

```text
G1 공공 API 데이터 수집
  -> raw/ 원본 파일 저장
G2 전처리 및 집계
  -> processed/ Parquet 파일 저장
  -> result/ssafy.duckdb 등록
```

운영 환경에서는 넓은 범위의 수집 기능을 일반 사용자에게 직접 노출하기보다, 스크립트나 스케줄러, 보호된 운영자 전용 엔드포인트로 관리하는 것이 적절합니다.

### G3-G4: 사용자/관리자 입력 기반 기능

G3와 G4는 G1-G2를 통해 데이터가 준비된 뒤 실행되는 애플리케이션 기능입니다.

```text
G3 이벤트 등록/선택
  -> 이벤트 메타데이터 DB 저장
G4 이벤트 기반 분석 실행
  -> processed/DuckDB 데이터 조회
  -> 분석 결과를 UI에 반환
```

이 기능들은 외부 공공 API를 반복 호출하지 않고 준비된 데이터를 조회하므로 일반 API/UI 기능으로 제공하기에 적합합니다.

## 주의사항

### API 할당량

- MOLIT: 1일 10,000 호출 제한
- JUSO: 일일 할당량 제한 있음

### 초기 데이터 수집 시간

- 테스트 수집: 1지역, 2년 기준 약 2~3분
- 전체 수집: 49개 수집 코드, 20년 이상 기준으로 오래 걸릴 수 있음

### 성능 팁

- DuckDB는 파일 기반 DB로 자동 저장됩니다.
- Parquet 분할(year/month/region)로 선택적 로드가 가능합니다.
- 대규모 쿼리는 `/analysis/stats/*` 또는 G4 분석 API처럼 집계 테이블 기반 엔드포인트 사용을 권장합니다.

## 트러블슈팅

### `manifest.json not found`

데이터를 먼저 수집해야 합니다.

```bash
python scripts/test_collection.py
```

또는:

```http
POST /api/batch/import/sale-data
```

### DuckDB 테이블이 비어있음

월별 요약 Parquet을 DuckDB에 등록합니다.

```http
POST /api/batch/register-parquet-files
```

### API 응답이 느림

DuckDB에서 너무 많은 레코드를 쿼리하는 중일 수 있습니다. `limit` 파라미터를 줄이거나 필터를 추가하세요.

## 작업 메모

- 기준금리 이벤트는 47건 적재 완료했습니다.
- 분석 window는 DB가 아니라 Spring/FastAPI 분석 요청 JSON에서 관리합니다.
- G4 이벤트월 기준 변화율 분석 API는 `/analysis/event-window`로 제공합니다.

## 라이선스 및 참고

- MOLIT 실거래가 API: 공공 데이터
- JUSO API: 행정안전부 공공 데이터

## Event Window Analysis Update

`POST /analysis/event-window` now returns additional G4-oriented metrics while keeping the existing event-month indexed baseline.

- `monthly[].price_yoy_pct`: same-month previous-year price change
- `monthly[].peer_avg_price_change_pct`: equal-weight average price change across requested regions for the same relative month
- `monthly[].excess_price_change_pct`: regional price change minus the peer average
- `window_summary.final_price_yoy_pct`: final-window YoY price change
- `window_summary.final_excess_price_change_pct`: final-window excess price change versus peer average
- `window_summary.reaction_direction`: first strong reaction direction
- `window_summary.reaction_role`: `leader`, `follower`, `synchronous`, or `no_clear_reaction`
- `propagation_candidates`: lagged same-direction propagation candidates based on monthly price return correlation
- `window_summary.warnings`: low-volume and fallback-baseline interpretation warnings

Low-volume months remain in the monthly output, but they are excluded from YoY, peer-average, reaction timing, and propagation calculations.

If a region does not have an exact `event_ym` row, the baseline falls back to the latest observed month on or before `event_ym`, and `baseline.baseline_source` records that choice.
