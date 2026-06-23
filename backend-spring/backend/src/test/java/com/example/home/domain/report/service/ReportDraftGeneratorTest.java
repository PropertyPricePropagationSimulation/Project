package com.example.home.domain.report.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.example.home.domain.report.dto.ReportDraft;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class ReportDraftGeneratorTest {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final ReportDraftGenerator generator = new ReportDraftGenerator();

    @Test
    void generatesDraftFromCachedAnalysisJson() throws Exception {
        ReportDraft draft = generator.generate(objectMapper.readTree("""
                {
                  "event": {"name": "기준금리 인하"},
                  "analysis": {"baseline_ym": "201907", "window_months": 12,
                    "low_volume_policy": "excluded"},
                  "summary": {"region_count": 49, "rising_region_count": 47,
                    "falling_region_count": 2, "complete_window_count": 49,
                    "avg_price_change_after_window_pct": 16.79,
                    "avg_volume_change_after_window_pct": 61.06},
                  "rankings": {
                    "top_price_rise": [{"dong_code": "41133", "final_price_change_pct": 40.86}],
                    "top_price_drop": [{"dong_code": "11110", "final_price_change_pct": -9.92}]
                  }
                }
                """));

        assertEquals("기준금리 인하 분석 리포트", draft.title());
        assertTrue(draft.keyFindings().stream().anyMatch(value -> value.contains("16.79%")));
        assertTrue(draft.keyFindings().stream().anyMatch(value -> value.contains("경기 성남시 중원구")));
        assertFalse(draft.keyFindings().stream().anyMatch(value -> value.contains("지역 코드")));
        assertEquals(2, draft.cautions().size());
    }
}
