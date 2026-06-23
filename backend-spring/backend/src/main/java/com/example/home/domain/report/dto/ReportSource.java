package com.example.home.domain.report.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record ReportSource(
        @JsonProperty("analysis_cache_id") Long analysisCacheId,
        @JsonProperty("event_id") Long eventId,
        @JsonProperty("window_months") Integer windowMonths,
        @JsonProperty("region_codes") List<String> regionCodes
) {
}
