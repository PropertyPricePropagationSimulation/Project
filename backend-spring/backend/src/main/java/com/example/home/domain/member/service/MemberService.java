package com.example.home.domain.member.service;

import com.example.home.domain.member.dto.MemberPasswordChangeRequest;
import com.example.home.domain.member.dto.MemberRequest;
import com.example.home.domain.member.dto.MemberResponse;
import com.example.home.domain.member.dto.MemberUpdateRequest;

public interface MemberService {

    MemberResponse findById(Long id);

    boolean existsById(Long id);

    boolean existsByEmail(String email);

    void register(MemberRequest request);

    void update(Long id, MemberUpdateRequest request);

    void changePassword(Long id, MemberPasswordChangeRequest request);
    
    void delete(Long id);
}
