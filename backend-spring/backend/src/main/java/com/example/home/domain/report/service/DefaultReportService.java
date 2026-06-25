package com.example.home.domain.report.service;

import com.example.home.domain.analysis.entity.AnalysisCache;
import com.example.home.domain.analysis.repository.AnalysisCacheRepository;
import com.example.home.domain.analysis.util.AnalysisCacheKey;
import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.dto.ReportDraft;
import com.example.home.domain.report.dto.ReportGeneration;
import com.example.home.domain.report.dto.ReportHistoryItem;
import com.example.home.domain.report.dto.ReportSource;
import com.example.home.domain.report.entity.ReportHistory;
import com.example.home.domain.report.repository.ReportHistoryRepository;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.example.home.global.util.PageResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.OffsetDateTime;
import java.util.List;
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
    private final ReportHistoryRepository reportHistoryRepository;
    private final ObjectMapper objectMapper;

    @Override
    public ReportDocument create(Long userId, CreateReportRequest request) {
        AnalysisCache cache = analysisCacheRepository.findByKey(
                request.eventId(),
                request.windowMonths(),
                AnalysisCacheKey.regionSignature(request.regionCodes()));
        if (cache == null) {
            throw new BusinessException(ErrorCode.NOT_FOUND,
                    "해당 조건의 분석 결과가 없습니다. 먼저 분석을 실행해 주세요.");
        }

        ReportHistory existing = reportHistoryRepository.findByUserIdAndAnalysisCacheId(userId, cache.getCacheId());
        if (existing != null) {
            if (existing.getDeletedAt() != null) {
                reportHistoryRepository.restoreByUserIdAndAnalysisCacheId(userId, cache.getCacheId());
            }
            return reportSeedStore.get(existing.getReportId());
        }

        JsonNode analysisResult = parseAnalysisResult(cache);
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
        reportHistoryRepository.save(ReportHistory.builder()
                .reportId(document.reportId())
                .userId(userId)
                .analysisCacheId(cache.getCacheId())
                .title(draft.title())
                .status(document.status())
                .build());
        return document;
    }

    @Override
    public ReportDocument get(String reportId) {
        return reportSeedStore.get(reportId);
    }

    @Override
    public PageResponse<ReportHistoryItem> getMyReports(Long userId, int page, int size) {
        int safePage = Math.max(1, page);
        int safeSize = Math.max(1, size);
        int offset = (safePage - 1) * safeSize;
        List<ReportHistoryItem> content = reportHistoryRepository.findAllByUserId(userId, offset, safeSize).stream()
                .map(ReportHistoryItem::from)
                .toList();
        return PageResponse.of(content, safePage, safeSize, reportHistoryRepository.countByUserId(userId));
    }

    @Override
    public void deleteMyReport(Long userId, String reportId) {
        ReportHistory history = reportHistoryRepository.findByUserIdAndReportId(userId, reportId);
        if (history == null || history.getDeletedAt() != null) {
            throw new BusinessException(ErrorCode.NOT_FOUND, "삭제할 리포트를 찾을 수 없습니다.");
        }
        reportHistoryRepository.softDelete(userId, reportId);
    }

    private JsonNode parseAnalysisResult(AnalysisCache cache) {
        try {
            JsonNode root = objectMapper.readTree(cache.getResultJson());
            if (root instanceof ObjectNode objectNode) {
                objectNode.put("analysis_cache_id", cache.getCacheId());
            }
            return root;
        } catch (JsonProcessingException e) {
            throw new BusinessException(ErrorCode.REPORT_ANALYSIS_RESULT_INVALID,
                    "분석 캐시 결과 JSON을 읽을 수 없습니다.");
        }
    }
}
