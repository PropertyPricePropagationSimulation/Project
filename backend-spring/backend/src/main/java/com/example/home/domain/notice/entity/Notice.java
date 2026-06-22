package com.example.home.domain.notice.entity;

import com.example.home.global.common.BaseTimeEntity;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Getter
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
public class Notice extends BaseTimeEntity {

    private Long noticeId;
    private String title;
    private Long writerId;  // 작성자 식별자(닉네임 변경 시 적용 가능하도록)
    private String writer;  // 작성자
    private String content;

}
