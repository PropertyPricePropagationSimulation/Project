package com.example.home.domain.analysis.util;

import java.util.List;
import java.util.Objects;

public final class AnalysisCacheKey {

    private AnalysisCacheKey() {
    }

    public static String regionSignature(List<String> regionCodes) {
        if (regionCodes == null || regionCodes.isEmpty()) {
            return "ALL";
        }

        return regionCodes.stream()
                .filter(Objects::nonNull)
                .distinct()
                .sorted()
                .collect(java.util.stream.Collectors.joining(","));
    }
}
