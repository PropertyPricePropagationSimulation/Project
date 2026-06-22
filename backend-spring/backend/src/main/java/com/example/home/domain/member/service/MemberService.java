package com.example.home.domain.member.service;

import com.example.home.domain.member.dto.MemberRequest;
import com.example.home.domain.member.dto.MemberResponse;

public interface MemberService {

    MemberResponse findById(Long id);

    boolean existsById(Long id);

    boolean existsByEmail(String email);

    void register(MemberRequest request);

    void update(Long id, MemberRequest request);

    void delete(Long id);
}
