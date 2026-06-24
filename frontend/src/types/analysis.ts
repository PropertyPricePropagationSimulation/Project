// ── UI 레이어 타입 ──────────────────────────────────────────────────────────
export interface District {
  name: string
  change: number  // final_price_change_pct (선택된 이벤트 기준)
  lag: number     // lag_months (null → 0)
  vol: number     // final_volume_change_pct
}

export interface MapEvent {
  id: number      // API event_id
  name: string
  short: string   // "YYYY.MM" 표시용
}

// ── 공통 래퍼 ─────────────────────────────────────────────────────────────────
export interface BaseResponse<T> {
  status: number
  code: string | null
  message: string
  detail: T
}

// ── 이벤트 목록 (/api/analysis/events) ────────────────────────────────────────
export interface ApiEvent {
  id: number
  name: string
  event_type: string
  event_date: string                // "YYYY-MM-DD"
  event_ym: string                  // "YYYYMM"
  source: string
  description: string
  detail: Record<string, unknown>   // event_type마다 구조 다름
}

export interface EventsListResponse {
  status: string
  count: number
  events: ApiEvent[]
}

// ── 분석 요청 (/api/analysis/event-window) ────────────────────────────────────
export interface EventWindowRequest {
  event_id: number
  window_months: 3 | 6 | 12
  region_codes?: string[]  // LAWD_CD 목록, 생략 시 전체
}

// ── 분석 응답 ─────────────────────────────────────────────────────────────────
export interface EventWindowResponse {
  status: string
  analysis_cache_id?: number
  event: Record<string, unknown>
  analysis: Record<string, unknown>
  data_range: Record<string, unknown>
  summary: Record<string, unknown>    // stage 7에서 AnalysisSummary로 구체화
  rankings: Record<string, unknown>   // stage 7에서 Rankings로 구체화
  regions: RegionResult[]
  result_count: number
  complete_window_count: number
  requested_region_count: number
}

export interface RegionResult {
  dong_code: string  // 구 단위 LAWD_CD 5자리 (예: "11680")
  baseline: Record<string, unknown>
  window_summary: WindowSummary
  monthly: MonthlyData[]
}

export interface WindowSummary {
  direction: 'rise' | 'drop' | 'flat'
  lag_months: number | null
  reaction_ym: string | null
  impact_score: number
  is_complete_window: boolean
  max_price_drop_pct: number
  max_price_rise_pct: number
  expected_month_count: number
  observed_month_count: number
  final_price_change_pct: number
  final_volume_change_pct: number
  final_deal_amount_change_pct: number
}

export interface MonthlyData {
  deal_count: number
  year_month: string
  is_low_volume: boolean
  relative_month: number
  avg_deal_amount: number
  avg_price_per_sqm: number
  median_deal_amount: number
  price_change_from_event_pct: number
  volume_change_from_event_pct: number
  deal_amount_change_from_event_pct: number
  median_price_change_from_event_pct: number
}
