package com.example.home.domain.auth.dto;

public record TokenResponse(
        String accessToken,
        String refreshToken,
        long expiresIn
) {
    public static TokenResponse of(String accessToken, String refreshToken, long expiresIn) {
        return new TokenResponse(accessToken, refreshToken, expiresIn);
    }
}
