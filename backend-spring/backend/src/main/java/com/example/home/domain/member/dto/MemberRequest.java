package com.example.home.domain.member.dto;

import java.time.LocalDate;

public record MemberRequest(
        String email,
        String password,
        String nickname,
        LocalDate birthDate
) {
}
