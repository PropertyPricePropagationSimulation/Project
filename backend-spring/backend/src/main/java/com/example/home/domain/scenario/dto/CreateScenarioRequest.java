package com.example.home.domain.scenario.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.util.List;

@Schema(
        description = """
                G7 시나리오 생성 요청입니다.

                사용 방식은 2가지입니다.
                1) 캐시 기반 호출: analysis_cache_id만 전달
                2) 직접 분석 기반 호출: event_id, window_months, region_codes 전달

                analysis_cache_id가 있으면 해당 캐시 결과를 우선 사용하며,
                event_id / window_months / region_codes는 현재 로직상 검증하지 않고 사용하지 않습니다.
                """
)
public record CreateScenarioRequest(
        @JsonProperty("analysis_cache_id")
        @JsonAlias("analysisCacheId")
        @Schema(
                example = "12",
                nullable = true,
                description = "기존 analysis 결과의 cache id입니다. 값이 있으면 scenario는 이 캐시 결과를 우선 사용합니다."
        )
        Long analysisCacheId,

        @JsonProperty("event_id")
        @JsonAlias("eventId")
        @Schema(
                example = "30",
                nullable = true,
                description = "analysis_cache_id가 없을 때 사용하는 이벤트 id입니다."
        )
        Long eventId,

        @JsonProperty("window_months")
        @JsonAlias("windowMonths")
        @Schema(
                example = "6",
                allowableValues = {"3", "6", "12"},
                nullable = true,
                description = "analysis_cache_id가 없을 때 사용하는 분석 기간(개월)입니다."
        )
        Integer windowMonths,

        @JsonProperty("region_codes")
        @JsonAlias("regionCodes")
        @Schema(
                nullable = true,
                example = "[\"11680\",\"11710\"]",
                description = "analysis_cache_id가 없을 때 사용할 지역 코드 목록입니다."
        )
        List<String> regionCodes,

        @JsonProperty("max_regions")
        @JsonAlias("maxRegions")
        @Min(1)
        @Max(5)
        @Schema(
                example = "4",
                description = "시뮬레이션에 사용할 반응성 상위 지역 수입니다."
        )
        Integer maxRegions,

        @JsonProperty("agents_per_region")
        @JsonAlias("agentsPerRegion")
        @Min(6)
        @Max(18)
        @Schema(
                example = "12",
                description = "선택된 각 지역에 배치할 총 에이전트 수입니다."
        )
        Integer agentsPerRegion
) {
    public boolean usesAnalysisCache() {
        return analysisCacheId != null;
    }

    public int resolvedMaxRegions() {
        return maxRegions == null ? 4 : maxRegions;
    }

    public int resolvedAgentsPerRegion() {
        return agentsPerRegion == null ? 12 : agentsPerRegion;
    }

    public boolean hasFreshAnalysisInputs() {
        return eventId != null && windowMonths != null;
    }
}
