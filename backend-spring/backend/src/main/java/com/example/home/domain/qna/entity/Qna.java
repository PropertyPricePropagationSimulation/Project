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
public class Qna extends BaseTimeEntity {

    private Long qnaId;
    private String title;
    private Long writerId;
    private String writer;
    private String content;
    private boolean answered;

}
