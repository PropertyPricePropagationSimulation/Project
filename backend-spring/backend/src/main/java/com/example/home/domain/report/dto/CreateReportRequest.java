package com.example.home.domain.report.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Schema(description = "Generate a report from a cached event-window analysis")
public record CreateReportRequest(
        @JsonProperty("event_id") @JsonAlias("eventId") @NotNull Long eventId,
        @JsonProperty("window_months") @JsonAlias("windowMonths") @NotNull Integer windowMonths,
        @JsonProperty("region_codes") @JsonAlias("regionCodes") List<String> regionCodes
) {
}
