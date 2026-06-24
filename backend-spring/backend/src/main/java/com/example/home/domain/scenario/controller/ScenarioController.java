package com.example.home.domain.scenario.controller;

import com.example.home.domain.scenario.dto.CreateScenarioRequest;
import com.example.home.domain.scenario.dto.ScenarioDocument;
import com.example.home.domain.scenario.dto.ScenarioRoundExplanation;
import com.example.home.domain.scenario.service.ScenarioService;
import com.example.home.global.util.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Scenario", description = "G7 시나리오 탐색 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/scenarios")
public class ScenarioController {

    private final ScenarioService scenarioService;

    @Operation(
            summary = "G7 시나리오 실행",
            description = """
                    반응성이 높은 지역을 선별한 뒤, 지역별 페르소나 에이전트 시뮬레이션을 생성합니다.

                    호출 방식은 2가지입니다.
                    1) 캐시 기반 호출
                       - analysis_cache_id만 전달
                       - 기존 analysis 결과를 바로 재사용

                    2) 직접 분석 기반 호출
                       - event_id, window_months, region_codes 전달
                       - scenario 생성 전에 analysis를 먼저 수행

                    권장 방식은 analysis 응답에서 받은 analysis_cache_id를 그대로 사용하는 것입니다.
                    """,
            requestBody = @io.swagger.v3.oas.annotations.parameters.RequestBody(
                    required = true,
                    content = @Content(
                            examples = {
                                    @ExampleObject(
                                            name = "캐시 기반 호출",
                                            summary = "analysis_cache_id만 사용하는 권장 방식",
                                            value = """
                                                    {
                                                      "analysis_cache_id": 12,
                                                      "max_regions": 4,
                                                      "agents_per_region": 12
                                                    }
                                                    """
                                    ),
                                    @ExampleObject(
                                            name = "직접 분석 기반 호출",
                                            summary = "cache id가 없을 때 event/window/regions로 직접 호출",
                                            value = """
                                                    {
                                                      "event_id": 30,
                                                      "window_months": 6,
                                                      "region_codes": ["11680", "11710"],
                                                      "max_regions": 4,
                                                      "agents_per_region": 12
                                                    }
                                                    """
                                    )
                            }
                    )
            )
    )
    @PostMapping
    public ResponseEntity<BaseResponse<ScenarioDocument>> create(@RequestBody @Valid CreateScenarioRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(BaseResponse.success("시나리오 생성 완료", scenarioService.create(request)));
    }

    @Operation(summary = "시나리오 조회", description = "seed에 저장된 G7 시나리오 결과를 조회합니다.")
    @GetMapping("/{scenarioId}")
    public ResponseEntity<BaseResponse<ScenarioDocument>> get(@PathVariable String scenarioId) {
        return ResponseEntity.ok(BaseResponse.success("시나리오 조회 완료", scenarioService.get(scenarioId)));
    }

    @Operation(
            summary = "시나리오 특정 라운드 AI 설명",
            description = """
                    특정 라운드의 전체 시장 분위기와 지역별 페르소나 행동 이유를 한 번에 설명합니다.

                    relativeMonth 예시:
                    - T-1 이면 -1
                    - T0 이면 0
                    - T+2 이면 2
                    """
    )
    @PostMapping("/{scenarioId}/rounds/{relativeMonth}/explanation")
    public ResponseEntity<BaseResponse<ScenarioRoundExplanation>> explainRound(
            @PathVariable String scenarioId,
            @PathVariable int relativeMonth) {
        return ResponseEntity.ok(BaseResponse.success(
                "라운드 AI 설명 생성 완료",
                scenarioService.explainRound(scenarioId, relativeMonth)));
    }
}
