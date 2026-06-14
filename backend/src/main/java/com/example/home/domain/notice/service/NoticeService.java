package com.example.home.domain.notice.service;

import com.example.home.domain.notice.dto.NoticeRequest;
import com.example.home.domain.notice.dto.NoticeResponse;
import com.example.home.global.util.PageResponse;

public interface NoticeService {

    NoticeResponse findById(Long id);

    PageResponse<NoticeResponse> findAll(int page, int size);

    void create(Long userId, NoticeRequest request);

    void update(Long id, NoticeRequest request);

    void delete(Long id);
}
