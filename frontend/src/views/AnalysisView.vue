<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { MapEvent } from '@/types/analysis'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useReportStore } from '@/stores/reportStore'
import ShockMap from '@/components/map/ShockMap.vue'
import EventSelector from '@/components/analysis/EventSelector.vue'
import MetricsPanel from '@/components/analysis/MetricsPanel.vue'
import TimelineSlider from '@/components/analysis/TimelineSlider.vue'
import WindowSelector from '@/components/analysis/WindowSelector.vue'
import ReportPreview from '@/components/report/ReportPreview.vue'
import '@/assets/styles/analysis.css'

const router      = useRouter()
const store       = useAnalysisStore()
const reportStore = useReportStore()

// ── 타임라인 월 목록 (window_months 기반 동적 생성) ─────────────────────────
const MONTHS = computed(() => {
  const pre  = ['T-3', 'T-2', 'T-1']
  const post = Array.from({ length: store.windowMonths }, (_, i) => `T+${i + 1}`)
  return [...pre, 'T+0', ...post]
})

// ── UI 상태 ────────────────────────────────────────────────────────────────
const selectedEvIdx = ref(0)
const curMonth      = ref(3)    // MONTHS 인덱스, T+0 = 3 고정
const playing       = ref(false)
const showLabels    = ref(true)

watch(() => store.windowMonths, () => {
  const max = MONTHS.value.length - 1
  if (curMonth.value > max) curMonth.value = max
})

// ── API 이벤트 → MapEvent 변환 ─────────────────────────────────────────────
const toShort = (ym: string) => ym.slice(0, 4) + '.' + ym.slice(4, 6)

const events = computed<MapEvent[]>(() =>
  store.events.map(e => ({
    id:    e.id,
    name:  e.name,
    short: toShort(e.event_ym),
  }))
)

const currentEvent = computed(() => events.value[selectedEvIdx.value])

watch(curMonth, m => { store.currentRelativeMonth = m - 3 })

// ── 이벤트 선택 ────────────────────────────────────────────────────────────
function onEventSelect(i: number) {
  const ev = events.value[i]
  if (!ev) return
  selectedEvIdx.value = i
  curMonth.value      = 3
  reportStore.reset()
  store.selectEvent(ev.id)
}

function onWindowMonthsChange(months: 3 | 6 | 12) {
  reportStore.reset()
  store.setWindowMonths(months)
}

async function handleReportAction() {
  if (reportStore.report) {
    await reportStore.download()
    return
  }
  if (store.selectedEventId === null || !store.analysisResult) return
  await reportStore.generate({
    event_id:      store.selectedEventId,
    window_months: store.windowMonths,
    region_codes:  store.regionCodes.length > 0 ? store.regionCodes : undefined,
  })
}

// ── 초기 로드 ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await store.fetchEvents()
  const first = events.value[0]
  if (first) store.selectEvent(first.id)
})
</script>

<template>
  <!-- 지도 초기화 로딩 -->
  <div id="loading">
    <div class="ld-title">ESTATEFLOW</div>
    <div class="ld-bar"><div class="ld-fill" id="ldFill" style="width:0%"></div></div>
    <div class="ld-txt" id="ldTxt">행정구역 데이터 로딩 중...</div>
  </div>

  <div v-if="store.loading" class="api-loading">분석 데이터 로딩 중...</div>
  <div v-if="store.error" class="api-error">{{ store.error }}</div>

  <ShockMap
    :regions="store.analysisResult?.regions ?? []"
    :current-relative-month="curMonth - 3"
    :show-labels="showLabels"
  />

  <div class="ui">
    <div class="hdr">
      <div class="logo-sq">EF</div>
      <div>
        <div class="logo-nm">EstateFlow</div>
        <div class="logo-sb">부동산 정책 충격 전파 분석</div>
      </div>
      <div class="hdiv"></div>
      <EventSelector
        :events="events"
        :model-value="selectedEvIdx"
        @update:model-value="onEventSelect"
      />
      <div class="hdr-r">
        <WindowSelector
          :model-value="store.windowMonths"
          @update:model-value="onWindowMonthsChange($event)"
        />
        <div class="hdiv-sm"></div>
        <button
          class="report-btn"
          :disabled="reportStore.loading || !store.analysisResult || store.loading"
          @click="handleReportAction"
        >
          {{ reportStore.loading ? '처리 중...' : reportStore.report ? 'PDF 다운로드' : 'AI 리포트 생성' }}
        </button>
        <div class="ltog" :class="{ on: showLabels }" @click="showLabels = !showLabels">
          <div class="tog-dot"></div>지역 라벨
        </div>
        <button class="search-btn" @click="router.push('/search')">거래 검색</button>
        <div class="live"><div class="ldot"></div>LIVE</div>
      </div>
    </div>

    <MetricsPanel
      :regions="store.analysisResult?.regions ?? []"
      :current-relative-month="curMonth - 3"
    />
    <ReportPreview
      v-if="reportStore.report"
      :report="reportStore.report"
      :downloading="reportStore.loading"
      @download="reportStore.download"
    />

      <TimelineSlider
      :months="MONTHS"
      :model-value="curMonth"
      :playing="playing"
      :current-event="currentEvent"
      @update:model-value="curMonth = $event"
      @update:playing="playing = $event"
    />
  </div>
  <div v-if="reportStore.error" class="report-error">{{ reportStore.error }}</div>
</template>
