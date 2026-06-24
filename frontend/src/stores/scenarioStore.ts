import axios from 'axios'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { createScenario, explainScenarioRound, getScenario } from '@/api/scenarioApi'
import type { ScenarioDocument, ScenarioRoundExplanation } from '@/types/scenario'

function errorMessage(error: unknown): string {
  if (axios.isAxiosError<{ message?: string }>(error)) {
    return error.response?.data?.message ?? error.message
  }
  return error instanceof Error ? error.message : '시나리오를 불러오지 못했습니다.'
}

export const useScenarioStore = defineStore('scenario', () => {
  const scenario = ref<ScenarioDocument | null>(null)
  const roundExplanation = ref<ScenarioRoundExplanation | null>(null)
  const loading = ref(false)
  const explanationLoading = ref(false)
  const error = ref<string | null>(null)
  const explanationError = ref<string | null>(null)

  const rounds = computed(() => scenario.value?.rounds ?? [])

  async function createFromAnalysisCache(analysisCacheId: number): Promise<ScenarioDocument | null> {
    loading.value = true
    error.value = null
    try {
      const response = await createScenario({
        analysis_cache_id: analysisCacheId,
        max_regions: 5,
        agents_per_region: 12,
      })
      scenario.value = response.detail
      roundExplanation.value = null
      return response.detail
    } catch (e) {
      error.value = errorMessage(e)
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchScenario(scenarioId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await getScenario(scenarioId)
      scenario.value = response.detail
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchRoundExplanation(relativeMonth: number): Promise<void> {
    if (!scenario.value) return
    explanationLoading.value = true
    explanationError.value = null
    try {
      const response = await explainScenarioRound(scenario.value.scenario_id, relativeMonth)
      roundExplanation.value = response.detail
    } catch (e) {
      explanationError.value = errorMessage(e)
    } finally {
      explanationLoading.value = false
    }
  }

  function reset(): void {
    scenario.value = null
    roundExplanation.value = null
    error.value = null
    explanationError.value = null
  }

  function clearRoundExplanation(): void {
    roundExplanation.value = null
    explanationError.value = null
  }

  return {
    scenario,
    rounds,
    roundExplanation,
    loading,
    explanationLoading,
    error,
    explanationError,
    createFromAnalysisCache,
    fetchScenario,
    fetchRoundExplanation,
    clearRoundExplanation,
    reset,
  }
})
