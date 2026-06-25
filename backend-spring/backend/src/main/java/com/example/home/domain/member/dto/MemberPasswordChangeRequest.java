package com.example.home.domain.member.dto;

public record MemberPasswordChangeRequest(
	String curPassword,
	String newPassword,
	String confirmPassword
	) { 
}
