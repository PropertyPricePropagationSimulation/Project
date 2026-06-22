package com.example.home.global.util;

import java.util.List;

public record PageResponse<T>(
    List<T> content,
    int page,
    int size,
    long totalCount
) {
    public static <T> PageResponse<T> of(List<T> content, int page, int size, long totalCount) {
        return new PageResponse<>(content, page, size, totalCount);
    }
}
