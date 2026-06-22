package com.example.home.global.exception;

import com.example.home.global.exception.docs.ErrorCode;
import com.example.home.global.util.BaseResponse;
import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    protected ResponseEntity<BaseResponse<?>> handleBusinessException(BusinessException e) {
        ErrorCode errorCode = e.getErrorCode();

        return ResponseEntity
            .status(errorCode.getStatus())
            .body(BaseResponse.fail(errorCode, e.getDetail()));
    }

    // 필수 파라미터 누락
    @ExceptionHandler(MissingServletRequestParameterException.class)
    protected ResponseEntity<BaseResponse<?>> handleMissingServletRequestParameter(MissingServletRequestParameterException e) {
        ErrorCode errorCode = ErrorCode.INVALID_INPUT;

        log.warn("MissingServletRequestParameterException: param={}", e.getParameterName());
        Map<String, String> detail = Map.of(
            "code", errorCode.getCode(),
            "detail", e.getParameterName() + " is missing"
        );
        return ResponseEntity
            .status(errorCode.getStatus())
            .body(BaseResponse.fail(errorCode, detail));
    }

    // Forbidden
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<BaseResponse<?>> handleAccessDeniedException(AccessDeniedException e) {
        ErrorCode errorCode = ErrorCode.FORBIDDEN_ERROR;

        return ResponseEntity
            .status(errorCode.getStatus())
            .body(BaseResponse.fail(errorCode));
    }

    // 서버 에러
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<BaseResponse<?>> handleAllExceptions(Exception e) {
        ErrorCode errorCode = ErrorCode.SERVER_ERROR;

        log.error("Unhandled Internal Server Error occurred:", e);

        return ResponseEntity
            .status(errorCode.getStatus())
            .body(BaseResponse.fail(errorCode));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    protected ResponseEntity<BaseResponse<?>> handleMethodArgumentNotValidException(MethodArgumentNotValidException e) {

        List<Map<String, String>> fieldErrors = e.getBindingResult().getFieldErrors().stream()
            .map(fe -> java.util.Map.of(
                "field", fe.getField(),
                "rejectedValue", String.valueOf(fe.getRejectedValue()),
                "reason", Objects.toString(fe.getDefaultMessage(), "")
            ))
            .toList();

        List<String> logLines = fieldErrors.stream()
            .map(fe -> String.format(
                "%s=%s (%s)",
                fe.get("field"),
                fe.get("rejectedValue"),
                fe.get("reason")
            ))
            .toList();

        log.warn("MethodArgumentNotValidException: {}", logLines);

        return ResponseEntity
            .status(ErrorCode.INVALID_INPUT.getStatus())
            .body(BaseResponse.fail(ErrorCode.INVALID_INPUT, fieldErrors));
    }

    @ExceptionHandler({
        HttpMessageNotReadableException.class,
        MethodArgumentTypeMismatchException.class,
        InvalidFormatException.class
    })
    protected ResponseEntity<BaseResponse<?>> handleTypeMismatch(Exception e) {
        String detail = "Type Mismatch";

        if (e instanceof HttpMessageNotReadableException hmr) {
            Throwable cause = hmr.getMostSpecificCause();
            if (cause instanceof InvalidFormatException ife) {
                detail = logInvalidFormat(ife);
            } else {
                log.warn("Unreadable request body: {}", hmr.getMessage());
            }
        }

        else if (e instanceof InvalidFormatException ife) {
            detail = logInvalidFormat(ife);
        }

        else if (e instanceof MethodArgumentTypeMismatchException matme) {
            Class<?> requiredType = matme.getRequiredType();
            String typeName = (requiredType != null) ? requiredType.getSimpleName() : "Unknown";

            detail = "param=" + matme.getName() + ", value=" + matme.getValue() + ", requiredType=" + typeName;
            log.warn("MethodArgumentTypeMismatchException: " + detail);
        }

        else {
            log.warn("Type mismatch or unreadable request body: {}", e.getMessage());
        }

        return ResponseEntity
            .status(ErrorCode.INVALID_INPUT.getStatus())
            .body(BaseResponse.fail(ErrorCode.INVALID_INPUT, detail));
    }

    private String logInvalidFormat(InvalidFormatException ife) {
        String fieldPath = ife.getPath().stream()
            .map(ref -> {
                if (ref.getFieldName() != null) {
                    return ref.getFieldName();
                } else {
                    // 배열 인덱스일 수 있음
                    return "[" + ref.getIndex() + "]";
                }
            })
            .collect(Collectors.joining("."));

        Object invalidValue = ife.getValue();
        Class<?> targetType = ife.getTargetType();

        String logMsg;

        if (targetType != null && targetType.isEnum()) {
            Object[] allowed = targetType.getEnumConstants();
            logMsg = "field=" + fieldPath+ " value=" + invalidValue + ", allowed=" + Arrays.toString(allowed);
            log.warn("Invalid enum value: " + logMsg);
        } else {
            logMsg = "field=" + fieldPath+ " value=" + invalidValue + ", allowed=" + (targetType != null ? targetType.getSimpleName() : "");
            log.warn("Invalid type value: {}", logMsg);
        }

        return logMsg;
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    protected ResponseEntity<BaseResponse<?>> handleDataIntegrityViolation(DataIntegrityViolationException e) {
        log.error("DataIntegrityViolationException: ", e);
        return ResponseEntity
            .status(ErrorCode.DUPLICATE_VALUE.getStatus())
            .body(BaseResponse.fail(ErrorCode.DUPLICATE_VALUE));
    }

}