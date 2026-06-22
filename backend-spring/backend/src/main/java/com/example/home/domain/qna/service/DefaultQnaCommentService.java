package com.example.home.domain.qna.service;

import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.domain.qna.dto.QnaCommentRequest;
import com.example.home.domain.qna.dto.QnaCommentResponse;
import com.example.home.domain.qna.entity.QnaComment;
import com.example.home.domain.qna.repository.QnaCommentRepository;
import com.example.home.domain.qna.repository.QnaRepository;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultQnaCommentService implements QnaCommentService {

    private final QnaCommentRepository qnaCommentRepository;
    private final QnaRepository qnaRepository;
    private final MemberRepository memberRepository;

    @Override
    public List<QnaCommentResponse> findByQnaId(Long qnaId) {
        if (qnaRepository.findById(qnaId) == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        return qnaCommentRepository.findByQnaId(qnaId).stream()
                .map(QnaCommentResponse::from)
                .toList();
    }

    @Override
    public void create(Long qnaId, Long userId, QnaCommentRequest request) {
        if (qnaRepository.findById(qnaId) == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        Member member = memberRepository.findById(userId);
        if (member == null) throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        QnaComment comment = QnaComment.builder()
                .qnaId(qnaId)
                .content(request.content())
                .writerId(member.getUserId())
                .writer(member.getNickname())
                .build();
        qnaCommentRepository.save(comment);
    }

    @Override
    public void update(Long commentId, Long userId, QnaCommentRequest request) {
        QnaComment comment = qnaCommentRepository.findById(commentId);
        if (comment == null) throw new BusinessException(ErrorCode.COMMENT_NOT_FOUND);
        if (!comment.getWriterId().equals(userId)) throw new BusinessException(ErrorCode.FORBIDDEN_ERROR);
        QnaComment updated = QnaComment.builder()
                .commentId(commentId)
                .content(request.content())
                .build();
        qnaCommentRepository.update(updated);
    }

    @Override
    public void delete(Long commentId, Long userId) {
        QnaComment comment = qnaCommentRepository.findById(commentId);
        if (comment == null) throw new BusinessException(ErrorCode.COMMENT_NOT_FOUND);
        if (!comment.getWriterId().equals(userId)) throw new BusinessException(ErrorCode.FORBIDDEN_ERROR);
        qnaCommentRepository.deleteById(commentId);
    }
}
