<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { MapEvent } from '@/types/analysis'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useReportStore } from '@/stores/reportStore'
import { useAuthStore } from '@/stores/authStore'
import AppHeader from '@/components/common/AppHeader.vue'
import ShockMap from '@/components/map/ShockMap.vue'
import EventSelector from '@/components/analysis/EventSelector.vue'
import MetricsPanel from '@/components/analysis/MetricsPanel.vue'
import TimelineSlider from '@/components/analysis/TimelineSlider.vue'
import ReportPreview from '@/components/report/ReportPreview.vue'
import '@/assets/styles/analysis.css'
import '@/assets/styles/tour.css'
import { useAnalysisTour } from '@/composables/useAnalysisTour'

const router      = useRouter()
const store       = useAnalysisStore()
const reportStore = useReportStore()
const authStore   = useAuthStore()
const { startTour, startTourIfFirst } = useAnalysisTour()

// ── 타임라인 월 목록 (window_months 기반 동적 생성) ─────────────────────────
const MONTHS = computed(() => {
  const pre  = ['T-3', 'T-2', 'T-1']
  const post = Array.from({ length: store.windowMonths }, (_, i) => `T+${i + 1}`)
  return [...pre, 'T+0', ...post]
})

// ── ctrl-bar 높이 추적 → MetricsPanel top 동적 계산 ───────────────────────
const ctrlBarRef  = ref<HTMLElement | null>(null)
const timelineRef = ref<HTMLElement | null>(null)
const panelTop    = ref(144) // AppHeader(60) + ctrl-bar 기본 높이(60) + margin(24)
const panelBottom = ref(116) // timeline 기본 높이 + margin(16)
let   ctrlBarRO:  ResizeObserver | null = null
let   timelineRO: ResizeObserver | null = null

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

// 분석 결과가 처음 들어온 뒤 투어 시작 — 데이터 없이 투어하면 메트릭 패널이 비어 있음
watch(
  () => store.analysisResult,
  (result) => {
    if (!result) return
    void startTourIfFirst()
  },
  { once: true },
)

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
  if (!authStore.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/analysis' } })
    return
  }
  if (store.selectedEventId === null || !store.analysisResult) return
  await reportStore.generate({
    event_id:      store.selectedEventId,
    window_months: store.windowMonths,
    region_codes:  store.regionCodes.length > 0 ? store.regionCodes : undefined,
  })
}

// ── 분석 지역 클릭 → 거래 검색 확인 모달 ─────────────────────────────────
type ConfirmState = { dong_code: string; name: string; yearMonth: string; displayYM: string }
const confirmState = ref<ConfirmState | null>(null)

function addMonths(ym: string, delta: number): string {
  const year  = parseInt(ym.slice(0, 4))
  const month = parseInt(ym.slice(4, 6))
  const d     = new Date(year, month - 1 + delta)
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}`
}

function onRegionClick({ dong_code, name }: { dong_code: string; name: string }) {
  const ev = store.events[selectedEvIdx.value]
  if (!ev) return
  const yearMonth = addMonths(ev.event_ym, curMonth.value - 3)
  const y = yearMonth.slice(0, 4)
  const m = parseInt(yearMonth.slice(4, 6))
  playing.value      = false
  confirmState.value = { dong_code, name, yearMonth, displayYM: `${y}년 ${m}월` }
}

function confirmSearch() {
  if (!confirmState.value) return
  const { dong_code, yearMonth } = confirmState.value
  confirmState.value = null
  window.open(`/search?regionCode=${dong_code}&yearMonth=${yearMonth}`, '_blank')
}

function cancelConfirm() {
  confirmState.value = null
}

// ── 초기 로드 ──────────────────────────────────────────────────────────────
onMounted(async () => {
  if (ctrlBarRef.value) {
    ctrlBarRO = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry) panelTop.value = 60 + Math.round(entry.contentRect.height) + 24
    })
    ctrlBarRO.observe(ctrlBarRef.value)
  }
  const timelineEl = (timelineRef.value as any)?.$el as HTMLElement | undefined
  if (timelineEl) {
    timelineRO = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry) panelBottom.value = Math.round(entry.contentRect.height) + 16
    })
    timelineRO.observe(timelineEl)
  }

  await store.fetchEvents()
  const first = events.value[0]
  if (first) store.selectEvent(first.id)
})

onUnmounted(() => {
  ctrlBarRO?.disconnect()
  timelineRO?.disconnect()
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
    :paused="confirmState !== null"
    :playing="playing"
    @region-click="onRegionClick"
  />

  <div class="ui">
    <AppHeader />

    <!-- ── Analysis Control Bar ───────────────────────────────────── -->
    <div ref="ctrlBarRef" class="ctrl-bar">
      <EventSelector
        :events="events"
        :model-value="selectedEvIdx"
        :window-months="store.windowMonths"
        @update:model-value="onEventSelect"
        @update:window-months="onWindowMonthsChange"
      />
      <div class="ctrl-bar-r">
        <div class="ctrl-bar-r-main">
          <button
            class="report-btn"
            data-tour="report-button"
            :disabled="reportStore.loading || !store.analysisResult || store.loading"
            @click="handleReportAction"
          >
            {{ reportStore.loading ? '처리 중...' : reportStore.report ? 'PDF 다운로드' : authStore.isLoggedIn ? 'AI 리포트 생성' : 'AI 리포트 (로그인 필요)' }}
          </button>
          <div class="ltog" :class="{ on: showLabels }" @click="showLabels = !showLabels">
            <div class="tog-dot"></div>지역 라벨
          </div>
        </div>
        <div class="ctrl-bar-r-sub">
          <div class="live"><div class="ldot"></div>LIVE</div>
          <button class="tour-btn" title="도움말" @click="startTour">?</button>
        </div>
      </div>
    </div>

    <MetricsPanel
      :regions="store.analysisResult?.regions ?? []"
      :current-relative-month="curMonth - 3"
      :style="{ top: panelTop + 'px', maxHeight: `calc(100vh - ${panelTop}px - ${panelBottom}px)` }"
    />
    <ReportPreview
      v-if="reportStore.report"
      :report="reportStore.report"
      :downloading="reportStore.loading"
      @download="reportStore.download"
    />

    <TimelineSlider
      ref="timelineRef"
      :months="MONTHS"
      :model-value="curMonth"
      :playing="playing"
      :current-event="currentEvent"
      @update:model-value="curMonth = $event"
      @update:playing="playing = $event"
    />
  </div>
  <div v-if="reportStore.error" class="report-error">{{ reportStore.error }}</div>

  <!-- ── 거래 검색 확인 모달 ──────────────────────────────────────────── -->
  <Transition name="av-modal">
    <div v-if="confirmState" class="av-modal-backdrop" @click.self="cancelConfirm">
      <div class="av-modal-card">
        <div class="av-modal-label">아파트 매매 거래 검색</div>
        <div class="av-modal-region">{{ confirmState.name }}</div>
        <div class="av-modal-ym">{{ confirmState.displayYM }}</div>
        <div class="av-modal-desc">해당 조건으로 거래 내역을 검색합니다.</div>
        <div class="av-modal-actions">
          <button class="av-modal-cancel" @click="cancelConfirm">취소</button>
          <button class="av-modal-confirm" @click="confirmSearch">검색하기</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.av-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(3px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.av-modal-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 32px 36px;
  min-width: 300px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
}
.av-modal-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 18px;
}
.av-modal-region {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}
.av-modal-ym {
  font-size: 16px;
  color: #64748b;
  margin-top: 4px;
}
.av-modal-desc {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 10px;
  margin-bottom: 28px;
}
.av-modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.av-modal-cancel {
  background: none;
  border: 1px solid #e2e8f0;
  color: #64748b;
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.12s, color 0.12s;
}
.av-modal-cancel:hover {
  border-color: #cbd5e1;
  color: #1e293b;
}
.av-modal-confirm {
  background: #3b82f6;
  border: none;
  color: #fff;
  padding: 9px 22px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.12s;
}
.av-modal-confirm:hover { background: #2563eb; }

/* 등장/퇴장 애니메이션 */
.av-modal-enter-active,
.av-modal-leave-active { transition: opacity 0.15s ease; }
.av-modal-enter-from,
.av-modal-leave-to { opacity: 0; }
.av-modal-enter-active .av-modal-card,
.av-modal-leave-active .av-modal-card { transition: transform 0.15s ease; }
.av-modal-enter-from .av-modal-card,
.av-modal-leave-to .av-modal-card { transform: scale(0.96) translateY(-6px); }
</style>
