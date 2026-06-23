package com.example.home.domain.report.service;

import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;

@Service
public class ReportValidationService {

    public void validateAiEnhancement(JsonNode enhancement) {
        if (!enhancement.isObject()
                || !hasText(enhancement, "executive_summary")
                || !enhancement.path("sections").isArray()
                || !enhancement.path("regional_trends").isArray()
                || !enhancement.path("cautions").isArray()) {
            throw new BusinessException(ErrorCode.SERVER_ERROR, "AI 리포트 응답 형식이 올바르지 않습니다.");
        }

        if (RegionNameResolver.containsRegionCode(enhancement.toString())) {
            throw new BusinessException(ErrorCode.SERVER_ERROR, "AI 리포트에 사용자용이 아닌 지역 코드가 포함됐습니다.");
        }
    }

    private boolean hasText(JsonNode node, String field) {
        return node.path(field).isTextual() && !node.path(field).asText().isBlank();
    }
}
