package com.example.home.domain.qna.dto;

import com.example.home.domain.qna.entity.QnaComment;
import java.time.LocalDateTime;

public record QnaCommentResponse(
        Long commentId,
        Long qnaId,
        String content,
        String writer,
        Long writerId,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static QnaCommentResponse from(QnaComment comment) {
        return new QnaCommentResponse(
                comment.getCommentId(),
                comment.getQnaId(),
                comment.getContent(),
                comment.getWriter(),
                comment.getWriterId(),
                comment.getCreatedAt(),
                comment.getUpdatedAt()
        );
    }
}
