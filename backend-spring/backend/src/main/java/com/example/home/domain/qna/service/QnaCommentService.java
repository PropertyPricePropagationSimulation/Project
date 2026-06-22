package com.example.home.domain.qna.service;

import com.example.home.domain.qna.dto.QnaCommentRequest;
import com.example.home.domain.qna.dto.QnaCommentResponse;
import java.util.List;

public interface QnaCommentService {

    List<QnaCommentResponse> findByQnaId(Long qnaId);

    void create(Long qnaId, Long userId, QnaCommentRequest request);

    void update(Long commentId, Long userId, QnaCommentRequest request);

    void delete(Long commentId, Long userId);
}
