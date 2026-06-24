package com.example.home.domain.scenario.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record ScenarioRoundExplanation(
        @JsonProperty("scenario_id") String scenarioId,
        String status,
        @JsonProperty("relative_month") Integer relativeMonth,
        String label,
        @JsonProperty("market_mood") String marketMood,
        String summary,
        List<ScenarioRoundExplanationRegion> regions
) {}
