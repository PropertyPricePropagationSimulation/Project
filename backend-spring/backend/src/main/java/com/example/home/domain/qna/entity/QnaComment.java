package com.example.home.domain.qna.entity;

import com.example.home.global.common.BaseTimeEntity;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Getter
@SuperBuilder
@AllArgsConstructor
@NoArgsConstructor
public class QnaComment extends BaseTimeEntity {
    private Long commentId;
    private Long qnaId;
    private String content;
    private String writer;
    private Long writerId;
}
