package com.example.home.domain.member.entity;

import com.example.home.global.common.BaseTimeEntity;
import com.example.home.global.enums.MemberRole;
import com.example.home.global.enums.MemberStatus;
import java.time.LocalDate;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Getter
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
public class Member extends BaseTimeEntity {

    private Long userId;
    private String email;
    private String password;
    private String nickname;
    private LocalDate birthDate;
    private MemberStatus memberStatus;
    private MemberRole memberRole;

}
