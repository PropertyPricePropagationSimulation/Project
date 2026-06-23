import axios from 'axios'
import type { BaseResponse } from '@/types/analysis'
import type { CreateReportRequest, ReportDocument } from '@/types/report'

const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 150_000,
})

export async function createReport(request: CreateReportRequest): Promise<BaseResponse<ReportDocument>> {
  const response = await http.post<BaseResponse<ReportDocument>>('/reports', request)
  return response.data
}

export async function downloadReportPdf(reportId: string): Promise<{ blob: Blob; filename?: string }> {
  const response = await http.get<Blob>(`/reports/${reportId}/pdf`, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] as string | undefined
  const filename = disposition?.match(/filename="?([^";]+)"?/)?.[1]
  return { blob: response.data, filename }
}
