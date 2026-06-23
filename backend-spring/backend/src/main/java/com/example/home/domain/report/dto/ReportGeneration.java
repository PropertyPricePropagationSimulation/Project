package com.example.home.domain.report.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ReportGeneration(
        @JsonProperty("prompt_version") String promptVersion,
        String model,
        @JsonProperty("ai_status") String aiStatus
) {
}
