package com.example.home.domain.scenario.service;

import com.example.home.domain.scenario.dto.ScenarioDocument;
import com.example.home.domain.scenario.dto.ScenarioPersonaBehaviorExplanation;
import com.example.home.domain.scenario.dto.ScenarioPersonaSnapshot;
import com.example.home.domain.scenario.dto.ScenarioRound;
import com.example.home.domain.scenario.dto.ScenarioRoundExplanation;
import com.example.home.domain.scenario.dto.ScenarioRoundExplanationRegion;
import com.example.home.domain.scenario.dto.ScenarioRoundRegion;
import com.example.home.domain.scenario.model.AgentStance;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

@Slf4j
@Service
@RequiredArgsConstructor
public class ScenarioAiExplanationService {

    private static final RestClient REST_CLIENT = createRestClient();

    private final ObjectMapper objectMapper;
    private final ScenarioPromptLoader promptLoader;

    @Value("${spring.ai.openai.chat.model:${spring.ai.openai.chat.options.model:unknown}}")
    private String model;

    @Value("${spring.ai.openai.api-key}")
    private String apiKey;

    @Value("${spring.ai.openai.base-url}")
    private String baseUrl;

    @Value("${spring.ai.openai.chat.completions-path:chat/completions}")
    private String completionsPath;

    public ScenarioRoundExplanation explain(ScenarioDocument document, ScenarioRound round) {
        try {
            String response = requestCompletion(buildUserPrompt(document, round));
            JsonNode parsed = parse(response);
            return toExplanation(document, round, parsed, "COMPLETED");
        } catch (Exception e) {
            log.warn("Scenario round AI explanation failed. Falling back to rule-based explanation.", e);
            return fallback(document, round);
        }
    }

    private String requestCompletion(String userPrompt) throws JsonProcessingException {
        Map<String, Object> request = Map.of(
                "model", model,
                "messages", List.of(
                        Map.of("role", "developer", "content", promptLoader.systemPrompt()),
                        Map.of("role", "user", "content", userPrompt)));

        String requestJson = objectMapper.writeValueAsString(request);

        ResponseEntity<String> responseEntity;
        try {
            responseEntity = REST_CLIENT.post()
                    .uri(completionsUrl())
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + apiKey)
                    .header(HttpHeaders.ACCEPT, MediaType.ALL_VALUE)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(requestJson)
                    .retrieve()
                    .toEntity(String.class);
        } catch (RestClientResponseException e) {
            log.warn("Scenario AI API error: status={}, body={}", e.getStatusCode(), e.getResponseBodyAsString(), e);
            throw e;
        }

        JsonNode response = objectMapper.readTree(responseEntity.getBody());
        JsonNode content = response.path("choices").path(0).path("message").path("content");
        if (content.isMissingNode() || content.asText().isBlank()) {
            throw new IllegalStateException("Scenario AI response has no usable content.");
        }
        return content.asText();
    }

    private String buildUserPrompt(ScenarioDocument document, ScenarioRound round) throws JsonProcessingException {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("scenario_id", document.scenarioId());
        payload.put("source", document.source());
        payload.put("selected_regions", document.selectedRegions());
        payload.put("round", round);

        return """
                아래 JSON은 특정 시나리오의 한 라운드 데이터입니다.
                반드시 한국어로 설명하세요.
                반드시 출력 스키마를 따라 JSON만 반환하세요.

                <output_schema>
                %s
                </output_schema>

                <scenario_round>
                %s
                </scenario_round>
                """.formatted(
                promptLoader.outputSchema(),
                objectMapper.writeValueAsString(payload));
    }

    private JsonNode parse(String response) throws JsonProcessingException {
        String normalized = response.trim()
                .replaceFirst("^```(?:json)?\\s*", "")
                .replaceFirst("\\s*```$", "");
        JsonNode root = objectMapper.readTree(normalized);
        if (!root.isObject() || !root.hasNonNull("summary") || !root.path("regions").isArray()) {
            throw new IllegalStateException("Scenario AI response schema is invalid.");
        }
        return root;
    }

    private ScenarioRoundExplanation toExplanation(
            ScenarioDocument document,
            ScenarioRound round,
            JsonNode parsed,
            String status) {
        List<ScenarioRoundExplanationRegion> regions = new ArrayList<>();
        for (JsonNode regionNode : parsed.path("regions")) {
            List<ScenarioPersonaBehaviorExplanation> personas = new ArrayList<>();
            for (JsonNode personaNode : regionNode.path("personas")) {
                personas.add(new ScenarioPersonaBehaviorExplanation(
                        personaNode.path("persona_type").asText(),
                        personaNode.path("persona_label").asText(),
                        personaNode.path("dominant_stance").asText(),
                        personaNode.path("explanation").asText()));
            }
            regions.add(new ScenarioRoundExplanationRegion(
                    regionNode.path("region_code").asText(),
                    regionNode.path("region_name").asText(),
                    regionNode.path("dominant_stance").asText(),
                    regionNode.path("region_explanation").asText(),
                    personas));
        }
        return new ScenarioRoundExplanation(
                document.scenarioId(),
                status,
                round.relativeMonth(),
                round.label(),
                round.marketMood(),
                parsed.path("summary").asText(),
                regions);
    }

    private ScenarioRoundExplanation fallback(ScenarioDocument document, ScenarioRound round) {
        List<ScenarioRoundExplanationRegion> regions = round.regions().stream()
                .map(this::fallbackRegion)
                .toList();

        String summary = "%s 시점에는 전체 시장 분위기가 '%s'로 나타났고, 반응성이 높은 지역들을 중심으로 페르소나별 행동 차이가 확인되었습니다."
                .formatted(round.label(), round.marketMood());

        return new ScenarioRoundExplanation(
                document.scenarioId(),
                "FALLBACK",
                round.relativeMonth(),
                round.label(),
                round.marketMood(),
                summary,
                regions);
    }

    private ScenarioRoundExplanationRegion fallbackRegion(ScenarioRoundRegion region) {
        List<ScenarioPersonaBehaviorExplanation> personas = region.personaStates().stream()
                .map(this::fallbackPersona)
                .toList();

        String regionExplanation = "%s은(는) 가격 변화 %.2f%%, 거래량 변화 %.2f%%, 영향도 %.2f를 보여 '%s' 성향이 우세하게 나타났습니다."
                .formatted(
                        region.regionName(),
                        zeroIfNull(region.priceChangePct()),
                        zeroIfNull(region.volumeChangePct()),
                        zeroIfNull(region.impactScore()),
                        region.dominantStance());

        return new ScenarioRoundExplanationRegion(
                region.regionCode(),
                region.regionName(),
                region.dominantStance(),
                regionExplanation,
                personas);
    }

    private ScenarioPersonaBehaviorExplanation fallbackPersona(ScenarioPersonaSnapshot persona) {
        String dominantStance = dominantStance(persona.stanceCounts());
        String explanation = "%s은(는) 평균 신호 %.2f와 행동 분포를 기준으로 '%s'가 가장 우세하게 나타났습니다."
                .formatted(persona.personaLabel(), zeroIfNull(persona.averageSignal()), dominantStance);
        return new ScenarioPersonaBehaviorExplanation(
                persona.personaType(),
                persona.personaLabel(),
                dominantStance,
                explanation);
    }

    private String dominantStance(Map<String, Integer> stanceCounts) {
        return stanceCounts.entrySet().stream()
                .max(Comparator.comparingInt(Map.Entry::getValue))
                .map(Map.Entry::getKey)
                .orElse(AgentStance.WATCH.name());
    }

    private double zeroIfNull(Double value) {
        return value == null ? 0.0 : value;
    }

    private String completionsUrl() {
        return baseUrl.endsWith("/") ? baseUrl + completionsPath : baseUrl + "/" + completionsPath;
    }

    private static RestClient createRestClient() {
        JdkClientHttpRequestFactory requestFactory = new JdkClientHttpRequestFactory();
        requestFactory.setReadTimeout(Duration.ofSeconds(90));
        return RestClient.builder().requestFactory(requestFactory).build();
    }
}
