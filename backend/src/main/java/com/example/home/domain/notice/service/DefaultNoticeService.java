package com.example.home.domain.notice.service;

import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.domain.notice.dto.NoticeRequest;
import com.example.home.domain.notice.dto.NoticeResponse;
import com.example.home.domain.notice.entity.Notice;
import com.example.home.domain.notice.repository.NoticeRepository;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import com.example.home.global.util.PageResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultNoticeService implements NoticeService {

    private final NoticeRepository noticeRepository;
    private final MemberRepository memberRepository;

    @Override
    public NoticeResponse findById(Long id) {
        Notice notice = noticeRepository.findById(id);
        if (notice == null) throw new BusinessException(ErrorCode.NOTICE_NOT_FOUND);
        return NoticeResponse.from(notice);
    }

    @Override
    public PageResponse<NoticeResponse> findAll(int page, int size) {
        int safePage = Math.max(1, page);
        int offset = (safePage - 1) * size;
        List<NoticeResponse> content = noticeRepository.findAll(offset, size).stream()
                .map(NoticeResponse::from)
                .toList();
        return PageResponse.of(content, safePage, size, noticeRepository.count());
    }

    @Override
    public void create(Long userId, NoticeRequest request) {
        Member member = memberRepository.findById(userId);
        if (member == null) throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        Notice notice = Notice.builder()
                .title(request.title())
                .content(request.content())
                .writerId(member.getUserId())
                .writer(member.getNickname())
                .build();
        noticeRepository.save(notice);
    }

    @Override
    public void update(Long id, NoticeRequest request) {
        if (noticeRepository.findById(id) == null) throw new BusinessException(ErrorCode.NOTICE_NOT_FOUND);
        Notice notice = Notice.builder()
                .noticeId(id)
                .title(request.title())
                .content(request.content())
                .build();
        noticeRepository.update(notice);
    }

    @Override
    public void delete(Long id) {
        if (noticeRepository.findById(id) == null) throw new BusinessException(ErrorCode.NOTICE_NOT_FOUND);
        noticeRepository.deleteById(id);
    }
}
