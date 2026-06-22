package com.example.home.domain.qna.controller;

import com.example.home.domain.qna.dto.QnaCommentRequest;
import com.example.home.domain.qna.dto.QnaCommentResponse;
import com.example.home.domain.qna.service.QnaCommentService;
import com.example.home.global.util.SecurityUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "QnaComment", description = "Q&A 댓글 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/qnas/{qnaId}/comments")
public class QnaCommentController {

    private final QnaCommentService qnaCommentService;

    @Operation(summary = "댓글 목록 조회")
    @GetMapping
    public ResponseEntity<List<QnaCommentResponse>> getComments(
            @Parameter(description = "Q&A ID") @PathVariable Long qnaId) {
        return ResponseEntity.ok(qnaCommentService.findByQnaId(qnaId));
    }

    @Operation(summary = "댓글 등록")
    @PostMapping
    public ResponseEntity<Void> createComment(
            @Parameter(description = "Q&A ID") @PathVariable Long qnaId,
            @RequestBody QnaCommentRequest request) {
        qnaCommentService.create(qnaId, SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @Operation(summary = "댓글 수정 (작성자 본인)")
    @PutMapping("/{commentId}")
    public ResponseEntity<Void> updateComment(
            @Parameter(description = "Q&A ID") @PathVariable Long qnaId,
            @Parameter(description = "댓글 ID") @PathVariable Long commentId,
            @RequestBody QnaCommentRequest request) {
        qnaCommentService.update(commentId, SecurityUtils.getCurrentUserId(), request);
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "댓글 삭제 (작성자 본인)")
    @DeleteMapping("/{commentId}")
    public ResponseEntity<Void> deleteComment(
            @Parameter(description = "Q&A ID") @PathVariable Long qnaId,
            @Parameter(description = "댓글 ID") @PathVariable Long commentId) {
        qnaCommentService.delete(commentId, SecurityUtils.getCurrentUserId());
        return ResponseEntity.noContent().build();
    }
}
