package com.example.home.domain.qna.controller;

import com.example.home.domain.qna.dto.QnaAnsweredRequest;
import com.example.home.domain.qna.dto.QnaRequest;
import com.example.home.domain.qna.dto.QnaResponse;
import com.example.home.domain.qna.service.QnaService;
import com.example.home.global.util.PageResponse;
import com.example.home.global.util.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
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

@Tag(name = "Qna", description = "Q&A API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/qnas")
public class QnaController {

    private final QnaService qnaService;

    @Operation(summary = "Q&A 목록 조회")
    @GetMapping
    public ResponseEntity<PageResponse<QnaResponse>> getQnas(
            @Parameter(description = "페이지 번호 (1부터 시작)") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "페이지 크기") @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(qnaService.findAll(page, size));
    }

    @Operation(summary = "Q&A 단건 조회")
    @GetMapping("/{id}")
    public ResponseEntity<QnaResponse> getQna(
            @Parameter(description = "Q&A ID") @PathVariable Long id) {
        return ResponseEntity.ok(qnaService.findById(id));
    }

    @Operation(summary = "Q&A 등록")
    @PostMapping
    public ResponseEntity<Void> createQna(@RequestBody QnaRequest request) {
        qnaService.create(SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @Operation(summary = "Q&A 수정 (작성자 본인)")
    @PutMapping("/{id}")
    public ResponseEntity<Void> updateQna(
            @Parameter(description = "Q&A ID") @PathVariable Long id,
            @RequestBody QnaRequest request) {
        qnaService.update(id, SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "답변 완료 여부 수정 (관리자 전용)")
    @PreAuthorize("hasRole('ADMIN')")
    @PatchMapping("/{id}/answered")
    public ResponseEntity<Void> updateAnswered(
            @Parameter(description = "Q&A ID") @PathVariable Long id,
            @RequestBody QnaAnsweredRequest request) {
        qnaService.updateAnswered(id, request.answered());
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "Q&A 삭제 (작성자 본인)")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteQna(
            @Parameter(description = "Q&A ID") @PathVariable Long id) {
        qnaService.delete(id, SecurityUtils.getCurrentUserId());
        return ResponseEntity.noContent().build();
    }
}
