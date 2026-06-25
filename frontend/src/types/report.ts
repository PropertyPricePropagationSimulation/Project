export interface CreateReportRequest {
  event_id: number
  window_months: number
  region_codes?: string[]
}

export interface ReportDocument {
  report_id: string
  status: 'COMPLETED' | 'DRAFT_FALLBACK'
  created_at: string
  analysis_cache_id?: number
  source?: ReportSource
  draft: ReportDraft
  ai_enhancement: ReportAiEnhancement | null
  analysis_result: ReportAnalysisResult
}

export interface ReportHistoryItem {
  report_id: string
  analysis_cache_id: number
  title: string
  status: 'COMPLETED' | 'DRAFT_FALLBACK'
  created_at: string
}

export interface ReportHistoryPage {
  content: ReportHistoryItem[]
  page: number
  size: number
  totalCount: number
}

export interface ReportSource {
  analysis_cache_id?: number
  event_id?: number
  window_months?: number
  region_codes?: string[]
}

export interface ReportDraft {
  title: string
  overview: string
}

export interface ReportAiEnhancement {
  executive_summary?: string
}

export interface ReportAnalysisResult {
  analysis_cache_id?: number
  summary?: ReportAnalysisSummary
}

export interface ReportAnalysisSummary {
  region_count?: number
  rising_region_count?: number
  falling_region_count?: number
  avg_price_change_after_window_pct?: number
  avg_volume_change_after_window_pct?: number
}
