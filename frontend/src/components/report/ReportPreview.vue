<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ReportDocument } from '@/types/report'

const props = defineProps<{
  report: ReportDocument
  downloading: boolean
}>()

const emit = defineEmits<{ download: [] }>()
const expanded = ref(false)

const summary = computed(() =>
  props.report.ai_enhancement?.executive_summary?.trim() || props.report.draft.overview,
)
const metrics = computed(() => props.report.analysis_result?.summary)
const statusLabel = computed(() =>
  props.report.status === 'COMPLETED' ? 'AI 고도화 완료' : '초안으로 생성됨',
)

function signed(value: number | undefined): string {
  if (value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}
</script>

<template>
  <aside class="report-preview">
    <div class="report-preview-head">
      <div>
        <span class="report-preview-kicker">AI REPORT</span>
        <h2>핵심 요약</h2>
      </div>
      <span class="report-preview-status" :class="{ fallback: report.status === 'DRAFT_FALLBACK' }">
        {{ statusLabel }}
      </span>
    </div>

    <p class="report-preview-title">{{ report.draft.title }}</p>
    <p class="report-preview-summary" :class="{ expanded }">{{ summary }}</p>
    <button v-if="summary.length > 260" class="report-preview-more" @click="expanded = !expanded">
      {{ expanded ? '접기' : '더보기' }}
    </button>

    <div v-if="metrics" class="report-preview-metrics">
      <div><span>분석 지역</span><strong>{{ metrics.region_count ?? '-' }}곳</strong></div>
      <div><span>상승 / 하락</span><strong>{{ metrics.rising_region_count ?? '-' }} / {{ metrics.falling_region_count ?? '-' }}</strong></div>
      <div><span>평균 가격 변동</span><strong :class="{ negative: (metrics.avg_price_change_after_window_pct ?? 0) < 0 }">{{ signed(metrics.avg_price_change_after_window_pct) }}</strong></div>
      <div><span>평균 거래량 변동</span><strong :class="{ negative: (metrics.avg_volume_change_after_window_pct ?? 0) < 0 }">{{ signed(metrics.avg_volume_change_after_window_pct) }}</strong></div>
    </div>

    <button class="report-preview-download" :disabled="downloading" @click="emit('download')">
      {{ downloading ? 'PDF 준비 중...' : 'PDF 다운로드' }}
    </button>
  </aside>
</template>
