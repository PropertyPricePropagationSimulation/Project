package com.example.home.domain.report.service;

import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.databind.JsonNode;
import com.openhtmltopdf.pdfboxout.PdfRendererBuilder;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.thymeleaf.context.Context;
import org.thymeleaf.spring6.SpringTemplateEngine;

/**
 * Renders reports through an HTML/CSS template. Layout concerns deliberately live in
 * {@code templates/report/report.html}, rather than in Java drawing coordinates.
 */
@Service
@RequiredArgsConstructor
public class ReportPdfService {

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
                sections.add(new SectionView(text(section, "title"), text(section, "content")));
            }
            for (JsonNode region : enhancement.path("regional_trends")) {
                List<String> evidence = new ArrayList<>();
                for (JsonNode item : region.path("evidence")) {
                    if (item.isTextual() && !item.asText().isBlank()) {
                        evidence.add(item.asText());
                    }
                }
                regionalTrends.add(new RegionalTrendView(
                        text(region, "region_name"),
                        text(region, "selection_reason"),
                        text(region, "trend"),
                        text(region, "comparative_interpretation"),
                        evidence));
            }
            cautions.addAll(textValues(enhancement.path("cautions")));
        } else {
            summary = report.draft().overview();
            for (String finding : report.draft().keyFindings()) {
                sections.add(new SectionView("", finding));
            }
            cautions.addAll(report.draft().cautions());
        }

        JsonNode analysisSummary = report.analysisResult() == null
                ? null
                : report.analysisResult().path("summary");
        return new ReportPdfView(
                report.draft().title(),
                report.createdAt(),
                report.source().windowMonths(),
                intValue(analysisSummary, "region_count"),
                intValue(analysisSummary, "rising_region_count"),
                intValue(analysisSummary, "falling_region_count"),
                summary,
                sections,
                regionalTrends,
                cautions);
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

    private int intValue(JsonNode node, String field) {
        if (node == null) {
            return 0;
        }
        return node.path(field).isInt() ? node.path(field).asInt() : 0;
    }

    public record ReportPdfView(
            String title,
            String createdAt,
            int windowMonths,
            int regionCount,
            int risingRegionCount,
            int fallingRegionCount,
            String summary,
            List<SectionView> sections,
            List<RegionalTrendView> regionalTrends,
            List<String> cautions) {
    }

    public record SectionView(String title, String content) {
    }

    public record RegionalTrendView(
            String regionName,
            String selectionReason,
            String trend,
            String comparativeInterpretation,
            List<String> evidence) {
    }
}
