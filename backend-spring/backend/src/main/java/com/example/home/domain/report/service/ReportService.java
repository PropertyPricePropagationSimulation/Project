package com.example.home.domain.report.service;

import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;
import com.example.home.domain.report.dto.ReportHistoryItem;
import com.example.home.global.util.PageResponse;

public interface ReportService {

    ReportDocument create(Long userId, CreateReportRequest request);

    ReportDocument get(String reportId);

    PageResponse<ReportHistoryItem> getMyReports(Long userId, int page, int size);

    void deleteMyReport(Long userId, String reportId);
}
