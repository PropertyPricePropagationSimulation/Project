import { http } from './http'
import type { BaseResponse } from '@/types/analysis'
import type { CreateReportRequest, ReportDocument, ReportHistoryPage } from '@/types/report'

export async function createReport(request: CreateReportRequest): Promise<BaseResponse<ReportDocument>> {
  const response = await http.post<BaseResponse<ReportDocument>>('/reports', request, { timeout: 150_000 })
  return response.data
}

export async function getMyReports(page = 1, size = 5): Promise<BaseResponse<ReportHistoryPage>> {
  const response = await http.get<BaseResponse<ReportHistoryPage>>('/reports/my', {
    params: { page, size },
    timeout: 30_000,
  })
  return response.data
}

export async function getReport(reportId: string): Promise<BaseResponse<ReportDocument>> {
  const response = await http.get<BaseResponse<ReportDocument>>(`/reports/${reportId}`, { timeout: 60_000 })
  return response.data
}

export async function deleteReport(reportId: string): Promise<void> {
  await http.delete(`/reports/${reportId}`, { timeout: 30_000 })
}

export async function downloadReportPdf(reportId: string): Promise<{ blob: Blob; filename?: string }> {
  const response = await http.get<Blob>(`/reports/${reportId}/pdf`, { responseType: 'blob', timeout: 60_000 })
  const disposition = response.headers['content-disposition'] as string | undefined
  const filename = disposition?.match(/filename="?([^";]+)"?/)?.[1]
  return { blob: response.data, filename }
}
