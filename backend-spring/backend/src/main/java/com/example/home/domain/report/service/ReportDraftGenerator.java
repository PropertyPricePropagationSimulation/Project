package com.example.home.domain.report.service;

import com.example.home.domain.report.dto.ReportDraft;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Component;

@Component
public class ReportDraftGenerator {

    public ReportDraft generate(JsonNode analysisResult) {
        JsonNode event = analysisResult.path("event");
        JsonNode analysis = analysisResult.path("analysis");
        JsonNode summary = analysisResult.path("summary");

        String eventName = text(event, "name", "정책 이벤트");
        String baselineYm = text(analysis, "baseline_ym", "-");
        int windowMonths = analysis.path("window_months").asInt();
        int regionCount = summary.path("region_count").asInt();
        int risingCount = summary.path("rising_region_count").asInt();
        int fallingCount = summary.path("falling_region_count").asInt();

        List<String> findings = new ArrayList<>();
        findings.add(String.format("분석 기준월은 %s이며, 관측 기간은 %d개월입니다.", baselineYm, windowMonths));
        findings.add(String.format("분석 지역 %d곳 중 %d곳은 상승, %d곳은 하락으로 집계되었습니다.",
                regionCount, risingCount, fallingCount));
        findings.add(String.format("분석 종료 시점의 평균 가격 변화율은 %s%%, 평균 거래량 변화율은 %s%%입니다.",
                percent(summary, "avg_price_change_after_window_pct"),
                percent(summary, "avg_volume_change_after_window_pct")));

        addRepresentativeFinding(findings, analysisResult.path("rankings").path("top_price_rise"), "가격 상승 폭이 가장 큰 지역");
        addRepresentativeFinding(findings, analysisResult.path("rankings").path("top_price_drop"), "가격 하락 폭이 가장 큰 지역");

        List<String> cautions = new ArrayList<>();
        cautions.add("본 결과는 이벤트 전후의 관측 변화이며, 이벤트와 가격 변화 사이의 인과관계를 단정하지 않습니다.");
        String lowVolumePolicy = text(analysis, "low_volume_policy", null);
        if (lowVolumePolicy != null) {
            cautions.add("저거래량 데이터는 분석 기준에 따라 일부 지표와 비교 계산에서 제외될 수 있습니다.");
        }
        int completeWindowCount = summary.path("complete_window_count").asInt(regionCount);
        if (completeWindowCount < regionCount) {
            cautions.add(String.format("%d개 지역은 전체 관측 기간이 채워지지 않아 해석에 주의가 필요합니다.",
                    regionCount - completeWindowCount));
        }

        String overview = String.format("%s 이후 %d개월 동안 지역별 가격 및 거래량 반응을 비교한 분석입니다.",
                eventName, windowMonths);
        return new ReportDraft(eventName + " 분석 리포트", overview, List.copyOf(findings), List.copyOf(cautions));
    }

    private void addRepresentativeFinding(List<String> findings, JsonNode ranking, String label) {
        if (!ranking.isArray() || ranking.isEmpty()) {
            return;
        }

        JsonNode top = ranking.get(0);
        String regionCode = text(top, "dong_code", "");
        findings.add(String.format("%s은 %s이며, 가격 변화율은 %s%%입니다.",
                label, RegionNameResolver.displayName(regionCode), percent(top, "final_price_change_pct")));
    }

    private String text(JsonNode node, String field, String fallback) {
        JsonNode value = node.path(field);
        return value.isMissingNode() || value.isNull() || value.asText().isBlank() ? fallback : value.asText();
    }

    private String percent(JsonNode node, String field) {
        JsonNode value = node.path(field);
        return value.isNumber() ? String.format(Locale.US, "%.2f", value.asDouble()) : "-";
    }
}
