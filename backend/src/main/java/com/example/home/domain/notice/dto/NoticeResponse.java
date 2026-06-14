package com.example.home.domain.notice.dto;

import com.example.home.domain.notice.entity.Notice;
import java.time.LocalDateTime;

public record NoticeResponse(
        Long noticeId,
        String title,
        Long writerId,
        String writer,
        String content,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static NoticeResponse from(Notice notice) {
        return new NoticeResponse(
                notice.getNoticeId(),
                notice.getTitle(),
                notice.getWriterId(),
                notice.getWriter(),
                notice.getContent(),
                notice.getCreatedAt(),
                notice.getUpdatedAt()
        );
    }
}
