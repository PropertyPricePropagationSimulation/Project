package com.example.home.domain.report.service;

import com.example.home.domain.analysis.entity.AnalysisCache;
import com.example.home.domain.analysis.repository.AnalysisCacheRepository;
import com.example.home.domain.analysis.util.AnalysisCacheKey;
import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.dto.ReportDraft;
import com.example.home.domain.report.dto.ReportGeneration;
import com.example.home.domain.report.dto.ReportSource;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.OffsetDateTime;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultReportService implements ReportService {

    private final AnalysisCacheRepository analysisCacheRepository;
    private final ReportDraftGenerator reportDraftGenerator;
    private final ReportAiService reportAiService;
    private final ReportSeedStore reportSeedStore;
    private final ObjectMapper objectMapper;

    @Override
    public ReportDocument create(CreateReportRequest request) {
        AnalysisCache cache = analysisCacheRepository.findByKey(
                request.eventId(),
                request.windowMonths(),
                AnalysisCacheKey.regionSignature(request.regionCodes()));
        if (cache == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND,
                    "해당 조건의 분석 결과가 없습니다. 먼저 분석을 실행해 주세요.");
        }

        JsonNode analysisResult = parseAnalysisResult(cache.getResultJson());
        ReportDraft draft = reportDraftGenerator.generate(analysisResult);
        ReportAiResult aiResult = reportAiService.enhance(draft, analysisResult);
        ReportDocument document = new ReportDocument(
                UUID.randomUUID().toString(),
                aiResult.status(),
                OffsetDateTime.now().toString(),
                new ReportSource(cache.getCacheId(), request.eventId(), request.windowMonths(), request.regionCodes()),
                draft,
                aiResult.enhancement(),
                new ReportGeneration(aiResult.promptVersion(), aiResult.model(), aiResult.status()),
                analysisResult);
        reportSeedStore.save(document);
        return document;
    }

    @Override
    public ReportDocument get(String reportId) {
        return reportSeedStore.get(reportId);
    }

    private JsonNode parseAnalysisResult(String resultJson) {
        try {
            return objectMapper.readTree(resultJson);
        } catch (JsonProcessingException e) {
            throw new BusinessException(ErrorCode.REPORT_ANALYSIS_RESULT_INVALID,
                    "분석 캐시 결과 JSON을 읽을 수 없습니다.");
        }
    }
}
