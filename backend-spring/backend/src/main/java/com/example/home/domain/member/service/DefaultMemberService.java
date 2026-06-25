package com.example.home.domain.member.service;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.home.domain.member.dto.MemberPasswordChangeRequest;
import com.example.home.domain.member.dto.MemberRequest;
import com.example.home.domain.member.dto.MemberResponse;
import com.example.home.domain.member.dto.MemberUpdateRequest;
import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.global.enums.MemberRole;
import com.example.home.global.enums.MemberStatus;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;

import lombok.RequiredArgsConstructor;

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
                .memberRole(MemberRole.USER)
                .build();
        memberRepository.save(member);
    }

    @Override
    public void update(Long id, MemberUpdateRequest request) {
        if (!existsById(id)) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        Member member = Member.builder()
                .userId(id)
                .nickname(request.nickname())
                .birthDate(request.birthDate())
                .build();
        memberRepository.update(member);
    }
    
    @Override
    public void changePassword(Long id, MemberPasswordChangeRequest request) {
        Member member = memberRepository.findById(id);
        if (member == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }

        validatePasswordChangeRequest(request);

        if (!passwordEncoder.matches(request.curPassword(), member.getPassword())) {
            throw new BusinessException(ErrorCode.INVALID_CURRENT_PASSWORD);
        }

        if (passwordEncoder.matches(request.newPassword(), member.getPassword())) {
            throw new BusinessException(ErrorCode.SAME_PASSWORD);
        }

        String encodedPassword = passwordEncoder.encode(request.newPassword());
        memberRepository.updatePassword(id, encodedPassword);
    }

    private void validatePasswordChangeRequest(MemberPasswordChangeRequest request) {
        if (request == null
                || request.curPassword() == null || request.curPassword().isBlank()
                || request.newPassword() == null || request.newPassword().isBlank()
                || request.confirmPassword() == null || request.confirmPassword().isBlank()) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        if (request.newPassword().length() < 8) {
            throw new BusinessException(ErrorCode.INVALID_PASSWORD_FORMAT);
        }

        if (!request.newPassword().equals(request.confirmPassword())) {
            throw new BusinessException(ErrorCode.PASSWORD_MISMATCH);
        }
    }

    @Override
    public void delete(Long id) {
        if (!existsById(id)) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        memberRepository.deleteById(id);
    }
}
