import { http } from './http'
import type { BaseResponse } from '@/types/analysis'
import type { CreateScenarioRequest, ScenarioDocument, ScenarioRoundExplanation } from '@/types/scenario'

export async function createScenario(request: CreateScenarioRequest): Promise<BaseResponse<ScenarioDocument>> {
  const response = await http.post<BaseResponse<ScenarioDocument>>('/scenarios', request, { timeout: 150_000 })
  return response.data
}

export async function getScenario(scenarioId: string): Promise<BaseResponse<ScenarioDocument>> {
  const response = await http.get<BaseResponse<ScenarioDocument>>(`/scenarios/${scenarioId}`, { timeout: 60_000 })
  return response.data
}

export async function explainScenarioRound(
  scenarioId: string,
  relativeMonth: number,
): Promise<BaseResponse<ScenarioRoundExplanation>> {
  const response = await http.post<BaseResponse<ScenarioRoundExplanation>>(
    `/scenarios/${scenarioId}/rounds/${relativeMonth}/explanation`,
    {},
    { timeout: 120_000 },
  )
  return response.data
}
