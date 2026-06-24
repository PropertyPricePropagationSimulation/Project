import axios from 'axios'
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { createReport, downloadReportPdf } from '@/api/reportApi'
import type { CreateReportRequest, ReportDocument } from '@/types/report'

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
  const loading = ref(false)
  const error = ref<string | null>(null)

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

  async function download(): Promise<void> {
    if (!report.value) return
    loading.value = true
    error.value = null
    try {
      const { blob, filename } = await downloadReportPdf(report.value.report_id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename ?? `estateflow-report-${report.value.report_id}.pdf`
      link.click()
      URL.revokeObjectURL(url)
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

  return { report, loading, error, generate, download, getAnalysisCacheId, reset }
})
