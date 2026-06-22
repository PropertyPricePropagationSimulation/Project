package com.example.home.domain.report.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

public record ReportDocument(
        @JsonProperty("report_id") String reportId,
        String status,
        @JsonProperty("created_at") String createdAt,
        ReportSource source,
        ReportDraft draft,
        @JsonProperty("ai_enhancement") JsonNode aiEnhancement,
        ReportGeneration generation,
        @JsonProperty("analysis_result") JsonNode analysisResult
) {
}
