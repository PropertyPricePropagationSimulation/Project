package com.example.home.domain.report.controller;

import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.dto.ReportHistoryItem;
import com.example.home.domain.report.service.ReportPdfService;
import com.example.home.domain.report.service.ReportService;
import com.example.home.global.util.BaseResponse;
import com.example.home.global.util.PageResponse;
import com.example.home.global.util.SecurityUtils;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.LinkedHashMap;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
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
            description = "같은 사용자가 같은 분석 캐시로 만든 리포트가 있으면 기존 seed 리포트를 재사용합니다.")
    @PreAuthorize("isAuthenticated()")
    @PostMapping
    public ResponseEntity<BaseResponse<Map<String, Object>>> create(@RequestBody @Valid CreateReportRequest request) {
        ReportDocument report = reportService.create(SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(BaseResponse.success("AI 리포트 생성 완료", responseBody(report)));
    }

    @Operation(summary = "내 리포트 목록 조회", description = "로그인 사용자가 생성한 AI 리포트 목록을 조회합니다.")
    @PreAuthorize("isAuthenticated()")
    @GetMapping("/my")
    public ResponseEntity<BaseResponse<PageResponse<ReportHistoryItem>>> getMyReports(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "5") int size) {
        return ResponseEntity.ok(BaseResponse.success(
                "리포트 목록 조회 완료",
                reportService.getMyReports(SecurityUtils.getCurrentUserId(), page, size)));
    }

    @Operation(summary = "리포트 조회", description = "seed에 저장된 초안/AI 고도화 결과를 조회합니다.")
    @GetMapping("/{reportId}")
    public ResponseEntity<BaseResponse<Map<String, Object>>> get(@PathVariable String reportId) {
        return ResponseEntity.ok(BaseResponse.success("리포트 조회 완료", responseBody(reportService.get(reportId))));
    }

    @Operation(summary = "내 리포트 삭제", description = "seed 파일은 유지하고 마이페이지 목록에서만 숨김 처리합니다.")
    @PreAuthorize("isAuthenticated()")
    @DeleteMapping("/{reportId}")
    public ResponseEntity<BaseResponse<?>> delete(@PathVariable String reportId) {
        reportService.deleteMyReport(SecurityUtils.getCurrentUserId(), reportId);
        return ResponseEntity.ok(BaseResponse.success("리포트 삭제 완료"));
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
        response.put("analysis_cache_id", report.source() != null ? report.source().analysisCacheId() : null);
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
