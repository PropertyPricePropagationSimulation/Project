package com.example.home.global.common;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public abstract class BaseTimeEntity {

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

}
