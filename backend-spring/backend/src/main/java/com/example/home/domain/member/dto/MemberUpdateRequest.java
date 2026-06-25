package com.example.home.domain.member.dto;

import java.time.LocalDate;

public record MemberUpdateRequest(
		String nickname,
		LocalDate birthDate
) {	
}