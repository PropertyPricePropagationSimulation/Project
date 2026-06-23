package com.example.home.domain.report.service;

import com.fasterxml.jackson.databind.JsonNode;

public record ReportAiResult(
        String status,
        String promptVersion,
        String model,
        JsonNode enhancement
) {
}
