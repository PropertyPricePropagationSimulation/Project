package com.example.home.domain.report.controller;

import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.service.ReportService;
import com.example.home.global.util.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
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

    @Operation(
            summary = "AI 리포트 생성",
            description = "캐시된 분석 결과로 초안을 생성한 뒤 AI가 지역별 동향을 고도화해 seed에 저장합니다. AI 호출에 실패하면 초안 리포트를 반환합니다.")
    @PostMapping
    public ResponseEntity<BaseResponse<ReportDocument>> create(@RequestBody @Valid CreateReportRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(BaseResponse.success("AI 리포트 생성 완료", reportService.create(request)));
    }

    @Operation(summary = "리포트 조회", description = "seed에 저장된 초안·AI 고도화 결과를 조회합니다.")
    @GetMapping("/{reportId}")
    public ResponseEntity<BaseResponse<ReportDocument>> get(@PathVariable String reportId) {
        return ResponseEntity.ok(BaseResponse.success("리포트 조회 완료", reportService.get(reportId)));
    }
}
