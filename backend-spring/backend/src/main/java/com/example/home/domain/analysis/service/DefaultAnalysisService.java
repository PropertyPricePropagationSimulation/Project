package com.example.home.domain.analysis.service;

import com.example.home.domain.analysis.client.AiServerClient;
import com.example.home.domain.analysis.dto.EventWindowRequest;
import com.example.home.domain.analysis.dto.EventWindowResponse;
import com.example.home.domain.analysis.entity.AnalysisCache;
import com.example.home.domain.analysis.repository.AnalysisCacheRepository;
import com.example.home.domain.analysis.util.AnalysisCacheKey;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class DefaultAnalysisService implements AnalysisService {

    private final AnalysisCacheRepository cacheRepository;
    private final AiServerClient aiServerClient;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    public EventWindowResponse analyze(EventWindowRequest request) {
        String signature = AnalysisCacheKey.regionSignature(request.regionCodes());

        AnalysisCache cached = cacheRepository.findByKey(request.eventId(), request.windowMonths(), signature);
        if (cached != null) {
            log.debug("캐시 히트: eventId={}, windowMonths={}, signature={}", request.eventId(), request.windowMonths(), signature);
            return parseJson(cached.getResultJson());
        }

        EventWindowResponse result = aiServerClient.requestEventWindowAnalysis(request);

        AnalysisCache cache = AnalysisCache.builder()
                .eventId(request.eventId())
                .windowMonths(request.windowMonths())
                .regionSignature(signature)
                .resultJson(toJson(result))
                .build();
        cacheRepository.save(cache);

        return result;
    }

    @Override
    public Map<String, Object> getEvents() {
        return aiServerClient.requestEvents();
    }

    private EventWindowResponse parseJson(String json) {
        try {
            return objectMapper.readValue(json, EventWindowResponse.class);
        } catch (JsonProcessingException e) {
            log.error("캐시 JSON 파싱 실패", e);
            throw new BusinessException(ErrorCode.SERVER_ERROR);
        }
    }

    private String toJson(EventWindowResponse result) {
        try {
            return objectMapper.writeValueAsString(result);
        } catch (JsonProcessingException e) {
            log.error("분석 결과 JSON 직렬화 실패", e);
            throw new BusinessException(ErrorCode.SERVER_ERROR);
        }
    }
}
