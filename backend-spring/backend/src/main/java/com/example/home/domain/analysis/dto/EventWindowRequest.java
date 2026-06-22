package com.example.home.domain.analysis.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Schema(
        name = "EventWindowAnalysisRequest",
        description = "FastAPI /analysis/event-window endpoint request format"
)
public record EventWindowRequest(
        @JsonProperty("event_id")
        @JsonAlias("eventId")
        @Schema(name = "event_id", example = "30", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull Long eventId,

        @JsonProperty("window_months")
        @JsonAlias("windowMonths")
        @Schema(name = "window_months", example = "3", allowableValues = {"3", "6", "12"}, requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull Integer windowMonths,

        @JsonProperty("region_codes")
        @JsonAlias("regionCodes")
        @Schema(name = "region_codes", example = "[\"11650\", \"11680\"]", nullable = true,
                description = "Optional LAWD_CD list. Send null or omit to analyze all regions.")
        List<String> regionCodes
) {}
