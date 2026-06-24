package com.example.home.domain.notice.controller;

import com.example.home.domain.notice.dto.NoticeRequest;
import com.example.home.domain.notice.dto.NoticeResponse;
import com.example.home.domain.notice.service.NoticeService;
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
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Notice", description = "공지사항 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/notices")
public class NoticeController {

    private final NoticeService noticeService;

    @Operation(summary = "공지사항 목록 조회")
    @GetMapping
    public ResponseEntity<PageResponse<NoticeResponse>> getNotices(
            @Parameter(description = "페이지 번호 (1부터 시작)") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "페이지 크기") @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(noticeService.findAll(page, size));
    }

    @Operation(summary = "공지사항 단건 조회")
    @GetMapping("/{id}")
    public ResponseEntity<NoticeResponse> getNotice(
            @Parameter(description = "공지사항 ID") @PathVariable Long id) {
        return ResponseEntity.ok(noticeService.findById(id));
    }

    @Operation(summary = "공지사항 등록 (관리자 전용)")
    @PreAuthorize("hasAuthority('ADMIN')")
    @PostMapping
    public ResponseEntity<Void> createNotice(@RequestBody NoticeRequest request) {
        noticeService.create(SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @Operation(summary = "공지사항 수정 (관리자 전용)")
    @PreAuthorize("hasAuthority('ADMIN')")
    @PutMapping("/{id}")
    public ResponseEntity<Void> updateNotice(
            @Parameter(description = "공지사항 ID") @PathVariable Long id,
            @RequestBody NoticeRequest request) {
        noticeService.update(id, request);
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "공지사항 삭제 (관리자 전용)")
    @PreAuthorize("hasAuthority('ADMIN')")
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteNotice(
            @Parameter(description = "공지사항 ID") @PathVariable Long id) {
        noticeService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
