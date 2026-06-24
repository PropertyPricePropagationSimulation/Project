package com.example.home.domain.scenario.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record ScenarioRoundExplanationRegion(
        @JsonProperty("region_code") String regionCode,
        @JsonProperty("region_name") String regionName,
        @JsonProperty("dominant_stance") String dominantStance,
        @JsonProperty("region_explanation") String regionExplanation,
        List<ScenarioPersonaBehaviorExplanation> personas
) {}
