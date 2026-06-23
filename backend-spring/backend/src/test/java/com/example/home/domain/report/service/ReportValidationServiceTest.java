package com.example.home.domain.report.service;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.example.home.global.exception.BusinessException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class ReportValidationServiceTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final ReportValidationService validationService = new ReportValidationService();

    @Test
    void acceptsStructuredEnhancementWithRegionNames() throws Exception {
        assertDoesNotThrow(() -> validationService.validateAiEnhancement(objectMapper.readTree("""
                {
                  "executive_summary": "경기 성남시 중원구의 반응이 비교적 빨랐습니다.",
                  "sections": [],
                  "regional_trends": [],
                  "cautions": []
                }
                """)));
    }

    @Test
    void rejectsEnhancementThatExposesRegionCodes() throws Exception {
        assertThrows(BusinessException.class, () -> validationService.validateAiEnhancement(objectMapper.readTree("""
                {
                  "executive_summary": "41133 지역의 반응이 비교적 빨랐습니다.",
                  "sections": [],
                  "regional_trends": [],
                  "cautions": []
                }
                """)));
    }
}
