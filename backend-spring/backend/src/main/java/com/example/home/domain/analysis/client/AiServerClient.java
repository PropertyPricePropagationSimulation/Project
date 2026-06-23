package com.example.home.domain.analysis.client;

import com.example.home.domain.analysis.dto.EventWindowRequest;
import com.example.home.domain.analysis.dto.EventWindowResponse;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@Slf4j
@Component
@RequiredArgsConstructor
public class AiServerClient {

    private static final Duration TIMEOUT = Duration.ofSeconds(30);

    private final WebClient aiServerWebClient;

    public EventWindowResponse requestEventWindowAnalysis(EventWindowRequest request) {
        AiServerRequest body = new AiServerRequest(
                request.eventId(),
                request.windowMonths(),
                request.regionCodes());

        try {
            EventWindowResponse response = aiServerWebClient.post()
                    .uri("/analysis/event-window")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(EventWindowResponse.class)
                    .timeout(TIMEOUT)
                    .block();
            if (response == null) {
                log.error("AI 분석 서버가 2xx 응답과 함께 빈 본문을 반환했습니다. request={}", body);
                throw new BusinessException(ErrorCode.AI_SERVER_ERROR);
            }
            return response;
        } catch (BusinessException e) {
            throw e;
        } catch (WebClientResponseException e) {
            log.error("AI 서버 응답 오류: type={}, status={}, headers={}, body={}",
                    e.getClass().getSimpleName(),
                    e.getStatusCode(),
                    e.getHeaders(),
                    e.getResponseBodyAsString(),
                    e);
            throw new BusinessException(ErrorCode.AI_SERVER_ERROR);
        } catch (Exception e) {
            log.error("AI 서버 호출 실패: type={}", e.getClass().getName(), e);
            throw new BusinessException(ErrorCode.AI_SERVER_ERROR);
        }
    }

    public Map<String, Object> requestEvents() {
        try {
            return aiServerWebClient.get()
                    .uri("/events/json")
                    .retrieve()
                    .bodyToMono(Map.class)
                    .timeout(TIMEOUT)
                    .map(m -> (Map<String, Object>) m)
                    .block();
        } catch (Exception e) {
            log.error("AI 서버 이벤트 조회 실패", e);
            throw new BusinessException(ErrorCode.AI_SERVER_ERROR);
        }
    }

    private record AiServerRequest(
            @JsonProperty("event_id") Long eventId,
            @JsonProperty("window_months") Integer windowMonths,
            @JsonProperty("region_codes") List<String> regionCodes) {
    }
}
