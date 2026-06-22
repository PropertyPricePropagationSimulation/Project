package com.example.home.global.exception.docs;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
@AllArgsConstructor
public enum ErrorCode {
    /*
	E 공통
	J Jwt
	A Auth
	M Member
	D db
	*/

    // 400 Bad Request
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "E400", "입력값이 올바르지 않습니다."),

    // 401 Unauthorized
    INVALID_TOKEN(HttpStatus.UNAUTHORIZED, "J401", "유효하지 않은 토큰입니다."),
    EXPIRED_TOKEN(HttpStatus.UNAUTHORIZED, "J402", "만료된 토큰입니다."),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "E401", "사용자 인증에 실패했습니다."),
    INVALID_CREDENTIALS(HttpStatus.UNAUTHORIZED, "A401", "이메일 또는 비밀번호가 올바르지 않습니다."),

    // 403 Forbidden
    FORBIDDEN_ERROR(HttpStatus.FORBIDDEN, "E403", "접근 권한이 없습니다."),

    // 404 Not Found
    NOT_FOUND(HttpStatus.NOT_FOUND, "E404", "정보가 존재하지 않습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "M404", "존재하지 않는 사용자입니다."),
    QNA_NOT_FOUND(HttpStatus.NOT_FOUND, "Q404", "존재하지 않는 질문입니다."),
    COMMENT_NOT_FOUND(HttpStatus.NOT_FOUND, "C404", "존재하지 않는 댓글입니다."),
    NOTICE_NOT_FOUND(HttpStatus.NOT_FOUND, "N404", "존재하지 않는 공지사항입니다."),

    // 409 Conflict
    DUPLICATE_VALUE(HttpStatus.CONFLICT, "M409", "중복된 값입니다."),

    // 500 Internal Server Error
    SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "E500", "서버 작업 중 예상치 못한 오류가 발생했습니다."),
    REDIS_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "E503", "인증 세션 저장에 실패했습니다."),
    ;

    private final HttpStatus status;
    private final String code;
    private final String message;

}
