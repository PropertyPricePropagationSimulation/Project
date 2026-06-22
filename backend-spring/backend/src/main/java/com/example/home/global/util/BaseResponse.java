package com.example.home.global.util;

import com.example.home.global.exception.docs.ErrorCode;
import org.springframework.http.HttpStatus;


public record BaseResponse<T>(
    int status,
    String code,
    String message,
    T detail
) {
    public static BaseResponse<?> success(String message) {
        return new BaseResponse<>(HttpStatus.OK.value(), null, message, null);
    }

    public static <T> BaseResponse<T> success(String message, T data) {
        return new BaseResponse<>(HttpStatus.OK.value(), null, message, data);
    }

    public static BaseResponse<?> fail(ErrorCode e) {
        return new BaseResponse<>(e.getStatus().value(), e.getCode(), e.getMessage(), null);
    }

    public static BaseResponse<?> fail(ErrorCode e, String message) {
        return new BaseResponse<>(e.getStatus().value(), e.getCode(), message, null);
    }

    public static <T> BaseResponse<T> fail(ErrorCode e, T detail) {
        return new BaseResponse<>(e.getStatus().value(), e.getCode(), e.getMessage(), detail);
    }
}
