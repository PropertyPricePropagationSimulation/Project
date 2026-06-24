<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useScenarioStore } from '@/stores/scenarioStore'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const selectedRelativeMonth = ref<number | null>(null)

const scenario = computed(() => scenarioStore.scenario)
const rounds = computed(() => scenarioStore.rounds)
const currentRound = computed(() =>
  rounds.value.find(round => round.relative_month === selectedRelativeMonth.value) ?? null,
)

function signed(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

async function loadScenario(): Promise<void> {
  const scenarioId = String(route.params.scenarioId ?? '')
  if (!scenarioId) {
    router.push('/mypage')
    return
  }

  await scenarioStore.fetchScenario(scenarioId)
  const firstRound = scenarioStore.rounds[0]
  if (!selectedRelativeMonth.value && firstRound) {
    selectedRelativeMonth.value = firstRound.relative_month
  }
}

async function handleExplainRound(): Promise<void> {
  if (selectedRelativeMonth.value === null) return
  await scenarioStore.fetchRoundExplanation(selectedRelativeMonth.value)
}

watch(selectedRelativeMonth, () => {
  scenarioStore.clearRoundExplanation()
})

onMounted(loadScenario)
</script>

<template>
  <div class="scenario-page">
    <AppHeader />

    <main class="scenario-main">
      <div class="scenario-inner">
        <section class="scenario-hero">
          <div>
            <p class="scenario-kicker">PERSONA ANALYSIS</p>
            <h1>리포트 기반 페르소나 시뮬레이션</h1>
            <p class="scenario-sub">
              분석 결과를 바탕으로 반응성이 높은 지역을 추리고, 실수요자·투자자·갈아타기 수요층이
              라운드별로 어떻게 움직이는지 확인합니다.
            </p>
          </div>

          <router-link to="/mypage" class="scenario-back">마이페이지로 돌아가기</router-link>
        </section>

        <div v-if="scenarioStore.loading" class="scenario-state">시나리오를 불러오는 중입니다...</div>
        <div v-else-if="scenarioStore.error" class="scenario-state error">{{ scenarioStore.error }}</div>

        <template v-else-if="scenario">
          <section class="scenario-summary">
            <div class="summary-card">
              <span>선정 지역 수</span>
              <strong>{{ scenario.final_summary.selected_region_count }}</strong>
            </div>
            <div class="summary-card">
              <span>라운드 수</span>
              <strong>{{ scenario.final_summary.round_count }}</strong>
            </div>
            <div class="summary-card">
              <span>가장 민감한 지역</span>
              <strong>{{ scenario.final_summary.most_reactive_region }}</strong>
            </div>
            <div class="summary-card">
              <span>전체 시장 분위기</span>
              <strong>{{ scenario.final_summary.dominant_market_mood }}</strong>
            </div>
          </section>

          <section class="scenario-section">
            <h2>선정된 지역</h2>
            <div class="region-grid">
              <article v-for="region in scenario.selected_regions" :key="region.region_code" class="region-card">
                <div class="region-head">
                  <strong>{{ region.region_name }}</strong>
                  <span>{{ region.region_code }}</span>
                </div>

                <div class="region-scores">
                  <span>투자 민감도 {{ region.speculation_score.toFixed(2) }}</span>
                  <span>안정성 {{ region.stability_score.toFixed(2) }}</span>
                  <span>이동 수요 {{ region.migration_score.toFixed(2) }}</span>
                </div>

                <ul class="region-reasons">
                  <li v-for="reason in region.selection_reasons" :key="reason">{{ reason }}</li>
                </ul>
              </article>
            </div>
          </section>

          <section class="scenario-section">
            <div class="round-header">
              <h2>라운드 선택</h2>
              <button
                class="explain-btn"
                :disabled="selectedRelativeMonth === null || scenarioStore.explanationLoading"
                @click="handleExplainRound"
              >
                {{ scenarioStore.explanationLoading ? '설명 생성 중...' : '이 라운드 AI 설명 보기' }}
              </button>
            </div>

            <div class="round-tabs">
              <button
                v-for="round in rounds"
                :key="round.relative_month"
                class="round-tab"
                :class="{ active: selectedRelativeMonth === round.relative_month }"
                @click="selectedRelativeMonth = round.relative_month"
              >
                {{ round.label }}
              </button>
            </div>

            <div v-if="currentRound" class="round-panel">
              <div class="round-overview">
                <div>
                  <span class="round-label">{{ currentRound.label }}</span>
                  <strong>{{ currentRound.market_mood }}</strong>
                </div>
                <p>{{ currentRound.narrative }}</p>
              </div>

              <div class="round-region-list">
                <article v-for="region in currentRound.regions" :key="region.region_code" class="round-region-card">
                  <div class="round-region-head">
                    <div>
                      <strong>{{ region.region_name }}</strong>
                      <span>{{ region.region_code }}</span>
                    </div>
                    <em>{{ region.dominant_stance }}</em>
                  </div>

                  <div class="round-metrics">
                    <span>가격 변화 {{ signed(region.price_change_pct) }}</span>
                    <span>거래량 변화 {{ signed(region.volume_change_pct) }}</span>
                    <span>영향 점수 {{ region.impact_score?.toFixed(2) ?? '-' }}</span>
                  </div>

                  <div class="persona-list">
                    <article
                      v-for="persona in region.persona_states"
                      :key="`${region.region_code}-${persona.persona_type}`"
                      class="persona-card"
                    >
                      <div class="persona-head">
                        <strong>{{ persona.persona_label }}</strong>
                        <span>{{ persona.total_agents }}명</span>
                      </div>

                      <div class="persona-stances">
                        <span v-for="(count, stance) in persona.stance_counts" :key="stance">{{ stance }} {{ count }}</span>
                      </div>

                      <p>평균 신호 {{ persona.average_signal?.toFixed(2) ?? '-' }}</p>
                    </article>
                  </div>
                </article>
              </div>
            </div>

            <div v-if="scenarioStore.explanationError" class="scenario-state error">{{ scenarioStore.explanationError }}</div>

            <section v-if="scenarioStore.roundExplanation" class="scenario-explanation">
              <h3>AI 라운드 설명</h3>
              <p class="explanation-summary">{{ scenarioStore.roundExplanation.summary }}</p>

              <div class="explanation-region-list">
                <article
                  v-for="region in scenarioStore.roundExplanation.regions"
                  :key="`${region.region_code}-${region.dominant_stance}`"
                  class="explanation-region-card"
                >
                  <div class="round-region-head">
                    <div>
                      <strong>{{ region.region_name }}</strong>
                      <span>{{ region.region_code }}</span>
                    </div>
                    <em>{{ region.dominant_stance }}</em>
                  </div>

                  <p class="region-text">{{ region.region_explanation }}</p>

                  <div class="explanation-personas">
                    <article
                      v-for="persona in region.personas"
                      :key="`${region.region_code}-${persona.persona_type}`"
                      class="explanation-persona-card"
                    >
                      <strong>{{ persona.persona_label }} · {{ persona.dominant_stance }}</strong>
                      <p>{{ persona.explanation }}</p>
                    </article>
                  </div>
                </article>
              </div>
            </section>
          </section>
        </template>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.scenario-page { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }
.scenario-main { flex: 1; padding: 40px 24px; }
.scenario-inner { max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
.scenario-hero,
.scenario-section,
.scenario-summary { background: #fff; border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.scenario-hero { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; padding: 28px; }
.scenario-kicker { font-size: 11px; font-weight: 700; letter-spacing: .12em; color: #3b82f6; margin-bottom: 8px; }
.scenario-hero h1 { font-size: 28px; color: #0f172a; margin-bottom: 10px; }
.scenario-sub { font-size: 14px; line-height: 1.7; color: #64748b; max-width: 720px; }
.scenario-back { text-decoration: none; font-size: 14px; color: #3b82f6; white-space: nowrap; }
.scenario-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 20px; }
.summary-card { background: #f8fafc; border-radius: 12px; padding: 18px; display: flex; flex-direction: column; gap: 8px; }
.summary-card span { font-size: 12px; color: #64748b; }
.summary-card strong { font-size: 18px; color: #0f172a; }
.scenario-section { padding: 24px; }
.scenario-section h2,
.scenario-explanation h3 { font-size: 18px; color: #0f172a; margin-bottom: 16px; }
.region-grid,
.round-region-list,
.explanation-region-list { display: grid; gap: 16px; }
.region-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.region-card,
.round-region-card,
.explanation-region-card { border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; }
.region-head,
.round-region-head,
.persona-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.region-head span,
.round-region-head span,
.persona-head span { font-size: 12px; color: #94a3b8; }
.region-scores,
.round-metrics,
.persona-stances { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; font-size: 13px; color: #475569; }
.region-reasons { margin-top: 14px; padding-left: 18px; color: #475569; font-size: 13px; line-height: 1.6; }
.round-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
.round-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
.round-tab,
.explain-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  border-radius: 10px;
  padding: 10px 14px;
  cursor: pointer;
  font-family: inherit;
}
.round-tab.active { background: #1e293b; color: #fff; border-color: #1e293b; }
.explain-btn { background: #3b82f6; color: #fff; border-color: #3b82f6; }
.explain-btn:disabled { opacity: .5; cursor: not-allowed; }
.round-panel { display: flex; flex-direction: column; gap: 16px; }
.round-overview { border-radius: 12px; background: #f8fafc; padding: 18px; display: flex; flex-direction: column; gap: 10px; }
.round-label { display: inline-block; font-size: 12px; color: #3b82f6; margin-right: 10px; }
.round-overview strong { color: #0f172a; }
.round-overview p,
.region-text,
.explanation-summary,
.explanation-persona-card p { color: #475569; line-height: 1.7; }
.persona-list,
.explanation-personas { display: grid; gap: 12px; margin-top: 14px; }
.persona-list { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.persona-card,
.explanation-persona-card { background: #f8fafc; border-radius: 12px; padding: 14px; }
.scenario-state { padding: 28px; background: #fff; border-radius: 16px; color: #64748b; }
.scenario-state.error { color: #dc2626; }
.scenario-explanation { margin-top: 22px; padding-top: 20px; border-top: 1px solid #e2e8f0; }

@media (max-width: 960px) {
  .scenario-summary,
  .region-grid,
  .persona-list { grid-template-columns: 1fr; }

  .scenario-hero,
  .round-header { flex-direction: column; align-items: stretch; }
}
</style>
