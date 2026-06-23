import axios from 'axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createReport, downloadReportPdf } from '@/api/reportApi'
import type { CreateReportRequest, ReportDocument } from '@/types/report'

function errorMessage(error: unknown): string {
  if (axios.isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? error.message
  }
  return error instanceof Error ? error.message : '리포트를 생성하지 못했습니다.'
}

export const useReportStore = defineStore('report', () => {
  const report = ref<ReportDocument | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

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

  function reset(): void {
    report.value = null
    error.value = null
  }

  return { report, loading, error, generate, download, reset }
})
