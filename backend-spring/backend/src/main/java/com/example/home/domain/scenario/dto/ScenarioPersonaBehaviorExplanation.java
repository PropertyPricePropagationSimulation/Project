package com.example.home.domain.scenario.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ScenarioPersonaBehaviorExplanation(
        @JsonProperty("persona_type") String personaType,
        @JsonProperty("persona_label") String personaLabel,
        @JsonProperty("dominant_stance") String dominantStance,
        String explanation
) {}
