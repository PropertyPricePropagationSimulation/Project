package com.example.home.domain.report.service;

import com.example.home.domain.report.dto.CreateReportRequest;
import com.example.home.domain.report.dto.ReportDocument;

public interface ReportService {

    ReportDocument create(CreateReportRequest request);

    ReportDocument get(String reportId);
}
