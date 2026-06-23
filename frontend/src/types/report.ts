export interface CreateReportRequest {
  event_id: number
  window_months: number
  region_codes?: string[]
}

export interface ReportDocument {
  report_id: string
  status: 'COMPLETED' | 'DRAFT_FALLBACK'
  created_at: string
  draft: ReportDraft
  ai_enhancement: ReportAiEnhancement | null
  analysis_result: ReportAnalysisResult
}

export interface ReportDraft {
  title: string
  overview: string
}

export interface ReportAiEnhancement {
  executive_summary?: string
}

export interface ReportAnalysisResult {
  summary?: ReportAnalysisSummary
}

export interface ReportAnalysisSummary {
  region_count?: number
  rising_region_count?: number
  falling_region_count?: number
  avg_price_change_after_window_pct?: number
  avg_volume_change_after_window_pct?: number
}
