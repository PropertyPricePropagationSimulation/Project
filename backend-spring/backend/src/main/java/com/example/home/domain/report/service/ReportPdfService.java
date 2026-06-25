package com.example.home.domain.report.service;

import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.databind.JsonNode;
import com.openhtmltopdf.pdfboxout.PdfRendererBuilder;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;
import org.thymeleaf.context.Context;
import org.thymeleaf.spring6.SpringTemplateEngine;

/**
 * Renders reports through an HTML/CSS template. Layout concerns deliberately live in
 * {@code templates/report/report.html}, rather than in Java drawing coordinates.
 */
@Service
@RequiredArgsConstructor
public class ReportPdfService {

    private static final Pattern HARD_TO_READ_UNIT_SENTENCE = Pattern.compile(
            "[^.!?。\\n]*(sqm|㎡|m2|m²|제곱미터|평당|면적당|단위면적)[^.!?。\\n]*[.!?。]?",
            Pattern.CASE_INSENSITIVE);
    private static final Pattern YEAR_MONTH = Pattern.compile("\\b(20\\d{2})년\\s*(0?[1-9]|1[0-2])월\\b");
    private static final Pattern PERCENT = Pattern.compile("([+-]?\\d+(?:\\.\\d+)?%)");
    private static final Pattern RISE_TERMS = Pattern.compile("(상승|증가|확대|급증|강세|반등)");
    private static final Pattern FALL_TERMS = Pattern.compile("(하락|감소|축소|둔화|약세|위축)");
    private static final Pattern MARKET_TERMS = Pattern.compile("(시장 전반|공통 반응|시장 반응|반응|가격|거래량|변동|분포|차이)");
    private static final Pattern TIME_TERMS = Pattern.compile("(시간적 흐름|시간 흐름|이벤트 직후|직후|관측 기간|종료 시점|반응 시점|지연|빠르게|늦게|흐름)");

    private final SpringTemplateEngine templateEngine;

    @Value("${report.pdf.font-path:C:/Windows/Fonts/malgun.ttf}")
    private String fontPath;

    public byte[] render(ReportDocument report) {
        Path fontFile = Path.of(fontPath);
        if (!Files.isRegularFile(fontFile)) {
            throw new BusinessException(ErrorCode.SERVER_ERROR,
                    "PDF 한글 폰트를 찾을 수 없습니다. REPORT_PDF_FONT_PATH를 설정해 주세요.");
        }

        try (ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            Context context = new Context();
            context.setVariable("report", toView(report));
            String html = templateEngine.process("report/report", context);

            PdfRendererBuilder builder = new PdfRendererBuilder();
            builder.useFastMode();
            builder.withHtmlContent(html, "");
            builder.useFont(fontFile.toFile(), "Noto Sans KR");
            builder.toStream(output);
            builder.run();
            return output.toByteArray();
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.SERVER_ERROR, "PDF 리포트를 생성하지 못했습니다.");
        }
    }

    private ReportPdfView toView(ReportDocument report) {
        JsonNode enhancement = report.aiEnhancement();
        boolean enhanced = enhancement != null && enhancement.isObject();
        List<SectionView> sections = new ArrayList<>();
        List<RegionalTrendView> regionalTrends = new ArrayList<>();
        List<String> cautions = new ArrayList<>();

        String summary;
        if (enhanced) {
            summary = text(enhancement, "executive_summary");
            for (JsonNode section : enhancement.path("sections")) {
                String content = text(section, "content");
                sections.add(new SectionView(
                        text(section, "title"),
                        readableText(content),
                        highlightBody(content)));
            }
            for (JsonNode region : enhancement.path("regional_trends")) {
                List<String> evidence = new ArrayList<>();
                for (JsonNode item : region.path("evidence")) {
                    if (item.isTextual() && !item.asText().isBlank()) {
                        evidence.add(highlightBody(item.asText()));
                    }
                }
                String selectionReason = text(region, "selection_reason");
                String trend = text(region, "trend");
                String comparativeInterpretation = text(region, "comparative_interpretation");
                regionalTrends.add(new RegionalTrendView(
                        text(region, "region_name"),
                        readableText(selectionReason),
                        highlightBody(selectionReason),
                        readableText(trend),
                        highlightBody(trend),
                        readableText(comparativeInterpretation),
                        highlightBody(comparativeInterpretation),
                        evidence));
            }
            cautions.addAll(highlightedTextValues(enhancement.path("cautions")));
        } else {
            summary = report.draft().overview();
            for (String finding : report.draft().keyFindings()) {
                sections.add(new SectionView("", readableText(finding), highlightBody(finding)));
            }
            for (String caution : report.draft().cautions()) {
                cautions.add(highlightBody(caution));
            }
        }

        JsonNode analysisSummary = report.analysisResult() == null
                ? null
                : report.analysisResult().path("summary");
        JsonNode topRise = report.analysisResult() == null ? null
                : report.analysisResult().path("rankings").path("top_price_rise");
        JsonNode topRiseRegion = topRise != null && topRise.isArray() && !topRise.isEmpty()
                ? topRise.get(0) : null;

        return new ReportPdfView(
                report.draft().title(),
                displayDate(report.createdAt()),
                report.source().windowMonths(),
                intValue(analysisSummary, "region_count"),
                intValue(analysisSummary, "rising_region_count"),
                intValue(analysisSummary, "falling_region_count"),
                signedPercent(analysisSummary, "avg_price_change_after_window_pct"),
                directionClass(analysisSummary, "avg_price_change_after_window_pct"),
                signedPercent(analysisSummary, "avg_volume_change_after_window_pct"),
                directionClass(analysisSummary, "avg_volume_change_after_window_pct"),
                topRiseRegionName(topRiseRegion),
                signedPercent(topRiseRegion, "final_price_change_pct"),
                readableText(summary),
                highlightBody(summary),
                sections,
                regionalTrends,
                cautions);
    }

    private String displayDate(String createdAt) {
        try {
            return OffsetDateTime.parse(createdAt).format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        } catch (Exception ignored) {
            return createdAt;
        }
    }

    private String topRiseRegionName(JsonNode region) {
        if (region == null) {
            return "집계 정보 없음";
        }
        String regionCode = text(region, "dong_code");
        return RegionNameResolver.regionNames().containsKey(regionCode)
                ? RegionNameResolver.displayName(regionCode) : "집계 정보 없음";
    }

    private String text(JsonNode node, String field) {
        JsonNode value = node.path(field);
        return value.isTextual() ? value.asText() : "";
    }

    private List<String> textValues(JsonNode nodes) {
        List<String> values = new ArrayList<>();
        for (JsonNode node : nodes) {
            if (node.isTextual() && !node.asText().isBlank()) {
                values.add(node.asText());
            }
        }
        return values;
    }

    private List<String> highlightedTextValues(JsonNode nodes) {
        List<String> values = new ArrayList<>();
        for (JsonNode node : nodes) {
            if (node.isTextual() && !node.asText().isBlank()) {
                values.add(highlightBody(node.asText()));
            }
        }
        return values;
    }

    private int intValue(JsonNode node, String field) {
        if (node == null) {
            return 0;
        }
        return node.path(field).isInt() ? node.path(field).asInt() : 0;
    }

    private String signedPercent(JsonNode node, String field) {
        if (node == null || !node.path(field).isNumber()) {
            return "-";
        }
        return String.format(Locale.US, "%+.2f%%", node.path(field).asDouble());
    }

    private String directionClass(JsonNode node, String field) {
        if (node == null || !node.path(field).isNumber()) {
            return "neutral";
        }
        double value = node.path(field).asDouble();
        if (value > 0) {
            return "rise";
        }
        if (value < 0) {
            return "fall";
        }
        return "neutral";
    }

    private String readableText(String value) {
        return removeHardToReadUnitSentences(value).trim();
    }

    private String highlightBody(String value) {
        String escaped = HtmlUtils.htmlEscape(readableText(value));
        escaped = YEAR_MONTH.matcher(escaped).replaceAll("<span class=\"hl-time\">$0</span>");
        escaped = PERCENT.matcher(escaped).replaceAll("<span class=\"hl-number\">$1</span>");
        escaped = RISE_TERMS.matcher(escaped).replaceAll("<span class=\"hl-rise\">$1</span>");
        escaped = FALL_TERMS.matcher(escaped).replaceAll("<span class=\"hl-fall\">$1</span>");
        escaped = TIME_TERMS.matcher(escaped).replaceAll("<span class=\"hl-time\">$1</span>");
        escaped = MARKET_TERMS.matcher(escaped).replaceAll("<span class=\"hl-market\">$1</span>");
        return escaped;
    }

    private String removeHardToReadUnitSentences(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        return HARD_TO_READ_UNIT_SENTENCE.matcher(value)
                .replaceAll("")
                .replaceAll("\\s{2,}", " ");
    }

    public record ReportPdfView(
            String title,
            String createdAt,
            int windowMonths,
            int regionCount,
            int risingRegionCount,
            int fallingRegionCount,
            String averagePriceChange,
            String averagePriceChangeClass,
            String averageVolumeChange,
            String averageVolumeChangeClass,
            String topRiseRegion,
            String topRisePercent,
            String summary,
            String highlightedSummary,
            List<SectionView> sections,
            List<RegionalTrendView> regionalTrends,
            List<String> cautions) {
    }

    public record SectionView(String title, String content, String highlightedContent) {
    }

    public record RegionalTrendView(
            String regionName,
            String selectionReason,
            String highlightedSelectionReason,
            String trend,
            String highlightedTrend,
            String comparativeInterpretation,
            String highlightedComparativeInterpretation,
            List<String> highlightedEvidence) {
    }
}
