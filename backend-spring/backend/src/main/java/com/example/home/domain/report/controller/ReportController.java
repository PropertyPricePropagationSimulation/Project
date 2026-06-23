package com.example.home.domain.report.controller;

import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.service.ReportPdfService;
import com.example.home.domain.report.service.ReportService;
import com.example.home.global.util.BaseResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.LinkedHashMap;
import java.util.Map;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Report", description = "분석 결과 기반 리포트 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/reports")
public class ReportController {

    private final ReportService reportService;
    private final ReportPdfService reportPdfService;
    private final ObjectMapper objectMapper;

    @Operation(
            summary = "AI 리포트 생성",
            description = "캐시된 분석 결과로 초안을 생성한 뒤 AI가 지역별 동향을 고도화해 seed에 저장합니다. AI 호출에 실패하면 초안 리포트를 반환합니다.")
    @PostMapping
    public ResponseEntity<BaseResponse<Map<String, Object>>> create(@RequestBody @Valid CreateReportRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(BaseResponse.success("AI 리포트 생성 완료", responseBody(reportService.create(request))));
    }

    @Operation(summary = "리포트 조회", description = "seed에 저장된 초안·AI 고도화 결과를 조회합니다.")
    @GetMapping("/{reportId}")
    public ResponseEntity<BaseResponse<Map<String, Object>>> get(@PathVariable String reportId) {
        return ResponseEntity.ok(BaseResponse.success("리포트 조회 완료", responseBody(reportService.get(reportId))));
    }

    @Operation(summary = "리포트 PDF 다운로드", description = "생성된 리포트를 PDF 파일로 반환합니다.")
    @GetMapping(value = "/{reportId}/pdf", produces = MediaType.APPLICATION_PDF_VALUE)
    public ResponseEntity<byte[]> downloadPdf(@PathVariable String reportId) {
        byte[] pdf = reportPdfService.render(reportService.get(reportId));
        String filename = "estateflow-report-" + reportId + ".pdf";
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment().filename(filename).build().toString())
                .contentType(MediaType.APPLICATION_PDF)
                .body(pdf);
    }

    private Map<String, Object> responseBody(ReportDocument report) {
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("report_id", report.reportId());
        response.put("status", report.status());
        response.put("created_at", report.createdAt());
        response.put("source", report.source());
        response.put("draft", report.draft());
        response.put("ai_enhancement", plainJson(report.aiEnhancement()));
        response.put("generation", report.generation());
        response.put("analysis_result", plainJson(report.analysisResult()));
        return response;
    }

    private Object plainJson(JsonNode node) {
        return node == null || node.isNull() ? null : objectMapper.convertValue(node, Object.class);
    }
}
