package com.example.home.domain.scenario.service;

import com.example.home.domain.analysis.dto.EventWindowRequest;
import com.example.home.domain.analysis.dto.EventWindowResponse;
import com.example.home.domain.analysis.entity.AnalysisCache;
import com.example.home.domain.analysis.repository.AnalysisCacheRepository;
import com.example.home.domain.analysis.service.AnalysisService;
import com.example.home.domain.analysis.util.AnalysisCacheKey;
import com.example.home.domain.scenario.dto.CreateScenarioRequest;
import com.example.home.domain.scenario.dto.ScenarioDocument;
import com.example.home.domain.scenario.dto.ScenarioRound;
import com.example.home.domain.scenario.dto.ScenarioRoundExplanation;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultScenarioService implements ScenarioService {

    private final AnalysisService analysisService;
    private final AnalysisCacheRepository analysisCacheRepository;
    private final ScenarioSimulationService scenarioSimulationService;
    private final ScenarioAiExplanationService scenarioAiExplanationService;
    private final ScenarioSeedStore scenarioSeedStore;

    @Override
    public ScenarioDocument create(CreateScenarioRequest request) {
        EventWindowResponse analysisResult;
        AnalysisCache cache;

        if (request.usesAnalysisCache()) {
            cache = analysisCacheRepository.findById(request.analysisCacheId());
            if (cache == null) {
                throw new BusinessException(ErrorCode.NOT_FOUND, "해당 분석 캐시 결과를 찾을 수 없습니다.");
            }
            analysisResult = analysisService.getCachedResult(request.analysisCacheId());
        } else {
            if (!request.hasFreshAnalysisInputs()) {
                throw new BusinessException(ErrorCode.INVALID_INPUT,
                        "analysisCacheId 또는 eventId/windowMonths를 함께 전달해야 합니다.");
            }
            EventWindowRequest analysisRequest = new EventWindowRequest(
                    request.eventId(),
                    request.windowMonths(),
                    request.regionCodes());
            analysisResult = analysisService.analyze(analysisRequest);
            cache = analysisCacheRepository.findByKey(
                    request.eventId(),
                    request.windowMonths(),
                    AnalysisCacheKey.regionSignature(request.regionCodes()));
        }

        Long cacheId = cache == null ? null : cache.getCacheId();
        Long sourceEventId = cache != null ? cache.getEventId() : request.eventId();
        Integer sourceWindowMonths = cache != null ? cache.getWindowMonths() : request.windowMonths();

        ScenarioDocument document = scenarioSimulationService.simulate(
                cacheId,
                sourceEventId,
                sourceWindowMonths,
                request.regionCodes(),
                request.resolvedAgentsPerRegion(),
                request.resolvedMaxRegions(),
                analysisResult);
        scenarioSeedStore.save(document);
        return document;
    }

    @Override
    public ScenarioDocument get(String scenarioId) {
        return scenarioSeedStore.get(scenarioId);
    }

    @Override
    public ScenarioRoundExplanation explainRound(String scenarioId, int relativeMonth) {
        ScenarioDocument document = scenarioSeedStore.get(scenarioId);
        ScenarioRound round = document.rounds().stream()
                .filter(item -> item.relativeMonth() != null && item.relativeMonth() == relativeMonth)
                .findFirst()
                .orElseThrow(() -> new BusinessException(
                        ErrorCode.NOT_FOUND,
                        "해당 relativeMonth에 해당하는 시나리오 라운드를 찾을 수 없습니다."));
        return scenarioAiExplanationService.explain(document, round);
    }
}
