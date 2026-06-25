package com.example.home.domain.report.dto;

import com.example.home.domain.report.entity.ReportHistory;
import com.fasterxml.jackson.annotation.JsonProperty;

public record ReportHistoryItem(
        @JsonProperty("report_id") String reportId,
        @JsonProperty("analysis_cache_id") Long analysisCacheId,
        String title,
        String status,
        @JsonProperty("created_at") String createdAt
) {
    public static ReportHistoryItem from(ReportHistory history) {
        return new ReportHistoryItem(
                history.getReportId(),
                history.getAnalysisCacheId(),
                history.getTitle(),
                history.getStatus(),
                history.getCreatedAt() == null ? null : history.getCreatedAt().toString());
    }
}
