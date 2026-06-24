export interface CreateScenarioRequest {
  analysis_cache_id?: number
  event_id?: number
  window_months?: number
  region_codes?: string[]
  max_regions?: number
  agents_per_region?: number
}

export interface ScenarioDocument {
  scenario_id: string
  status: string
  created_at: string
  source: ScenarioSource
  selected_regions: ScenarioRegionProfile[]
  rounds: ScenarioRound[]
  final_summary: ScenarioFinalSummary
}

export interface ScenarioSource {
  analysis_cache_id?: number
  event_id?: number
  window_months?: number
  requested_region_codes?: string[]
  selected_region_codes?: string[]
  agents_per_region?: number
}

export interface ScenarioRegionProfile {
  region_code: string
  region_name: string
  speculation_score: number
  stability_score: number
  migration_score: number
  persona_distribution: Record<string, number>
  selection_reasons: string[]
}

export interface ScenarioRound {
  relative_month: number
  label: string
  market_mood: string
  narrative: string
  regions: ScenarioRoundRegion[]
}

export interface ScenarioRoundRegion {
  region_code: string
  region_name: string
  price_change_pct: number | null
  volume_change_pct: number | null
  impact_score: number | null
  persona_states: ScenarioPersonaSnapshot[]
  dominant_stance: string
}

export interface ScenarioPersonaSnapshot {
  persona_type: string
  persona_label: string
  total_agents: number
  stance_counts: Record<string, number>
  average_signal: number | null
}

export interface ScenarioFinalSummary {
  selected_region_count: number
  round_count: number
  key_takeaways: string[]
  most_reactive_region: string
  dominant_market_mood: string
}

export interface ScenarioRoundExplanation {
  scenario_id: string
  status: string
  relative_month: number
  label: string
  market_mood: string
  summary: string
  regions: ScenarioRoundExplanationRegion[]
}

export interface ScenarioRoundExplanationRegion {
  region_code: string
  region_name: string
  dominant_stance: string
  region_explanation: string
  personas: ScenarioPersonaBehaviorExplanation[]
}

export interface ScenarioPersonaBehaviorExplanation {
  persona_type: string
  persona_label: string
  dominant_stance: string
  explanation: string
}
