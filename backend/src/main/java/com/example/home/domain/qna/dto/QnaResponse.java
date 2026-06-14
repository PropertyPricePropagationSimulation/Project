package com.example.home.domain.qna.dto;

import com.example.home.domain.qna.entity.Qna;
import java.time.LocalDateTime;

public record QnaResponse(
        Long qnaId,
        String title,
        Long writerId,
        String writer,
        String content,
        boolean answered,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static QnaResponse from(Qna qna) {
        return new QnaResponse(
                qna.getQnaId(),
                qna.getTitle(),
                qna.getWriterId(),
                qna.getWriter(),
                qna.getContent(),
                qna.isAnswered(),
                qna.getCreatedAt(),
                qna.getUpdatedAt()
        );
    }
}
