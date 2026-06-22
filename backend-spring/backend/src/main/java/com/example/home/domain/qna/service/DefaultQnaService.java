package com.example.home.domain.qna.service;

import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.domain.qna.dto.QnaRequest;
import com.example.home.domain.qna.dto.QnaResponse;
import com.example.home.domain.qna.entity.Qna;
import com.example.home.domain.qna.repository.QnaRepository;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.example.home.global.util.PageResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultQnaService implements QnaService {

    private final QnaRepository qnaRepository;
    private final MemberRepository memberRepository;

    @Override
    public QnaResponse findById(Long id) {
        Qna qna = qnaRepository.findById(id);
        if (qna == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        return QnaResponse.from(qna);
    }

    @Override
    public PageResponse<QnaResponse> findAll(int page, int size) {
        int safePage = Math.max(1, page);
        int offset = (safePage - 1) * size;
        List<QnaResponse> content = qnaRepository.findAll(offset, size).stream()
                .map(QnaResponse::from)
                .toList();
        return PageResponse.of(content, safePage, size, qnaRepository.count());
    }

    @Override
    public void create(Long userId, QnaRequest request) {
        Member member = memberRepository.findById(userId);
        if (member == null) throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        Qna qna = Qna.builder()
                .title(request.title())
                .content(request.content())
                .writerId(member.getUserId())
                .writer(member.getNickname())
                .answered(false)
                .build();
        qnaRepository.save(qna);
    }

    @Override
    public void update(Long id, Long userId, QnaRequest request) {
        Qna qna = qnaRepository.findById(id);
        if (qna == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        if (!qna.getWriterId().equals(userId)) throw new BusinessException(ErrorCode.FORBIDDEN_ERROR);
        Qna updated = Qna.builder()
                .qnaId(id)
                .title(request.title())
                .content(request.content())
                .build();
        qnaRepository.update(updated);
    }

    @Override
    public void updateAnswered(Long id, boolean answered) {
        if (qnaRepository.findById(id) == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        qnaRepository.updateAnswered(id, answered);
    }

    @Override
    public void delete(Long id, Long userId) {
        Qna qna = qnaRepository.findById(id);
        if (qna == null) throw new BusinessException(ErrorCode.QNA_NOT_FOUND);
        if (!qna.getWriterId().equals(userId)) throw new BusinessException(ErrorCode.FORBIDDEN_ERROR);
        qnaRepository.deleteById(id);
    }
}
