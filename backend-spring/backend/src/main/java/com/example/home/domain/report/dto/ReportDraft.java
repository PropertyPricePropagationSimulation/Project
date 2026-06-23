package com.example.home.domain.report.dto;

import java.util.List;

public record ReportDraft(
        String title,
        String overview,
        List<String> keyFindings,
        List<String> cautions
) {
}
