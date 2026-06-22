package com.example.home.domain.member.service;

import com.example.home.domain.member.dto.MemberRequest;
import com.example.home.domain.member.dto.MemberResponse;
import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.global.enums.MemberRole;
import com.example.home.global.enums.MemberStatus;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DefaultMemberService implements MemberService {

    private final MemberRepository memberRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public MemberResponse findById(Long id) {
        Member member = memberRepository.findById(id);
        if(member == null)
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        return MemberResponse.from(member);
    }

    @Override
    public boolean existsById(Long id) {
        Member member = memberRepository.findById(id);
        if(member == null)
            return false;
        return true;
    }

    @Override
    public boolean existsByEmail(String email) {
        return memberRepository.existsByEmail(email);
    }

    @Override
    public void register(MemberRequest request) {
        if (memberRepository.existsByEmail(request.email())) {
            throw new BusinessException(ErrorCode.DUPLICATE_VALUE);
        }
        Member member = Member.builder()
                .email(request.email())
                .password(passwordEncoder.encode(request.password()))
                .nickname(request.nickname())
                .birthDate(request.birthDate())
                .memberStatus(MemberStatus.ACTIVE)
                .memberRole(MemberRole.ROLE_USER)
                .build();
        memberRepository.save(member);
    }

    @Override
    public void update(Long id, MemberRequest request) {
        if (!existsById(id)) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        Member member = Member.builder()
                .userId(id)
                .nickname(request.nickname())
                .build();
        memberRepository.update(member);
    }

    @Override
    public void delete(Long id) {
        if (!existsById(id)) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        memberRepository.deleteById(id);
    }
}
