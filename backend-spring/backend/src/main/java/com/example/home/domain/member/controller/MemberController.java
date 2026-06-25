package com.example.home.domain.member.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.home.domain.member.dto.MemberPasswordChangeRequest;
import com.example.home.domain.member.dto.MemberRequest;
import com.example.home.domain.member.dto.MemberResponse;
import com.example.home.domain.member.dto.MemberUpdateRequest;
import com.example.home.domain.member.service.MemberService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

@Tag(name = "Member", description = "회원 관리 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/members")
public class MemberController {

	private final MemberService memberService;

	@Operation(summary = "회원 조회", description = "ID로 회원 정보를 조회합니다.")
	@ApiResponse(responseCode = "200", description = "조회 성공")
	@GetMapping("/{id}")
	public ResponseEntity<MemberResponse> getMember(@Parameter(description = "회원 ID") @PathVariable Long id) {
		return ResponseEntity.ok(memberService.findById(id));
	}

	@Operation(summary = "이메일 중복 확인", description = "회원가입 전 이메일 중복 여부를 확인합니다.")
	@ApiResponse(responseCode = "200", description = "중복 여부 반환 (true = 이미 존재)")
	@GetMapping("/check-email")
	public ResponseEntity<Boolean> checkEmail(@Parameter(description = "확인할 이메일 주소") @RequestParam String email) {
		return ResponseEntity.ok(memberService.existsByEmail(email));
	}

	@Operation(summary = "회원가입", description = "새 회원을 등록합니다.")
	@ApiResponse(responseCode = "201", description = "등록 성공")
	@PostMapping
	public ResponseEntity<Void> register(@RequestBody MemberRequest request) {
		memberService.register(request);
		return ResponseEntity.status(HttpStatus.CREATED).build();
	}

	@Operation(summary = "회원 정보 수정", description = "회원 닉네임과 생년월일을 수정합니다.")
	@ApiResponse(responseCode = "200", description = "수정 성공")
	@PutMapping("/{id}")
	public ResponseEntity<Void> update(
			@Parameter(description = "회원 ID") 
			@PathVariable Long id,
			@RequestBody MemberUpdateRequest request) {
		memberService.update(id, request);
		return ResponseEntity.ok().build();
	}

	@Operation(summary = "비밀번호 변경", description = "현재 비밀번호 확인 후 새 비밀번호로 변경합니다.")
	@ApiResponse(responseCode = "204", description = "변경 성공")
	@PatchMapping("/{id}/password")
	public ResponseEntity<Void> changePassword(
			@Parameter(description = "회원 ID") 
			@PathVariable Long id,
			@RequestBody MemberPasswordChangeRequest request) {
		memberService.changePassword(id, request);
		return ResponseEntity.noContent().build();
	}

	@Operation(summary = "회원 탈퇴", description = "회원을 삭제합니다.")
	@ApiResponse(responseCode = "204", description = "삭제 성공")
	@DeleteMapping("/{id}")
	public ResponseEntity<Void> delete(@Parameter(description = "회원 ID") @PathVariable Long id) {
		memberService.delete(id);
		return ResponseEntity.noContent().build();
	}

}
