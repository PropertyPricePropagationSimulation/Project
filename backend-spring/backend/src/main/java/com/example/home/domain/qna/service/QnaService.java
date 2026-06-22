package com.example.home.domain.qna.service;

import com.example.home.domain.qna.dto.QnaRequest;
import com.example.home.domain.qna.dto.QnaResponse;
import com.example.home.global.util.PageResponse;

public interface QnaService {

    QnaResponse findById(Long id);

    PageResponse<QnaResponse> findAll(int page, int size);

    void create(Long userId, QnaRequest request);

    void update(Long id, Long userId, QnaRequest request);

    void updateAnswered(Long id, boolean answered);

    void delete(Long id, Long userId);
}
