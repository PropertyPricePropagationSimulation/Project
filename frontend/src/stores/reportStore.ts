import axios from 'axios'
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { createReport, deleteReport, downloadReportPdf, getMyReports, getReport } from '@/api/reportApi'
import type { CreateReportRequest, ReportDocument, ReportHistoryItem } from '@/types/report'

const REPORT_STORAGE_KEY = 'estateflow:report'

function errorMessage(error: unknown): string {
  if (axios.isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? error.message
  }
  return error instanceof Error ? error.message : '리포트를 생성하지 못했습니다.'
}

function readStoredReport(): ReportDocument | null {
  if (typeof window === 'undefined') return null
  const raw = sessionStorage.getItem(REPORT_STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as ReportDocument
  } catch {
    sessionStorage.removeItem(REPORT_STORAGE_KEY)
    return null
  }
}

export const useReportStore = defineStore('report', () => {
  const report = ref<ReportDocument | null>(readStoredReport())
  const reports = ref<ReportHistoryItem[]>([])
  const reportPage = ref(1)
  const reportPageSize = ref(5)
  const reportTotalCount = ref(0)
  const loading = ref(false)
  const listLoading = ref(false)
  const error = ref<string | null>(null)
  const listError = ref<string | null>(null)

  watch(report, value => {
    if (typeof window === 'undefined') return
    if (value) {
      sessionStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(value))
    } else {
      sessionStorage.removeItem(REPORT_STORAGE_KEY)
    }
  }, { deep: true })

  async function generate(request: CreateReportRequest): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await createReport(request)
      report.value = response.detail
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchMyReports(page = reportPage.value): Promise<void> {
    listLoading.value = true
    listError.value = null
    try {
      const response = await getMyReports(page, reportPageSize.value)
      reports.value = response.detail?.content ?? []
      reportPage.value = response.detail?.page ?? page
      reportPageSize.value = response.detail?.size ?? reportPageSize.value
      reportTotalCount.value = response.detail?.totalCount ?? 0
    } catch (e) {
      listError.value = errorMessage(e)
    } finally {
      listLoading.value = false
    }
  }

  async function fetchReport(reportId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await getReport(reportId)
      report.value = response.detail
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function download(reportId?: string): Promise<void> {
    const targetReportId = reportId ?? report.value?.report_id
    if (!targetReportId) return
    loading.value = true
    error.value = null
    try {
      const { blob, filename } = await downloadReportPdf(targetReportId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename ?? `estateflow-report-${targetReportId}.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function remove(reportId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await deleteReport(reportId)
      if (report.value?.report_id === reportId) {
        report.value = null
      }
      const nextPage = reports.value.length === 1 && reportPage.value > 1
        ? reportPage.value - 1
        : reportPage.value
      await fetchMyReports(nextPage)
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  function getAnalysisCacheId(): number | null {
    return report.value?.analysis_cache_id
      ?? report.value?.source?.analysis_cache_id
      ?? report.value?.analysis_result?.analysis_cache_id
      ?? null
  }

  function reset(): void {
    report.value = null
    error.value = null
  }

  return {
    report,
    reports,
    reportPage,
    reportPageSize,
    reportTotalCount,
    loading,
    listLoading,
    error,
    listError,
    generate,
    fetchMyReports,
    fetchReport,
    download,
    remove,
    getAnalysisCacheId,
    reset,
  }
})
