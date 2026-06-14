package com.example.home.domain.auth.service;

import com.example.home.domain.auth.dto.LoginRequest;
import com.example.home.domain.auth.dto.RegisterRequest;
import com.example.home.domain.auth.dto.TokenResponse;
import com.example.home.domain.auth.provider.AuthTokenProvider;
import com.example.home.domain.member.entity.Member;
import com.example.home.domain.member.repository.MemberRepository;
import com.example.home.global.enums.MemberRole;
import com.example.home.global.enums.MemberStatus;
import com.example.home.global.exception.BusinessException;
import com.example.home.global.exception.docs.ErrorCode;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class AuthService {

    private final MemberRepository memberRepository;
    private final AuthTokenProvider authTokenProvider;
    private final RedisTemplate<String, String> redisTemplate;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public TokenResponse login(LoginRequest request) {
        Member member = memberRepository.findByEmail(request.email());
        if (member == null || !passwordEncoder.matches(request.password(), member.getPassword())) {
            throw new BusinessException(ErrorCode.INVALID_CREDENTIALS);
        }
        return issueToken(member.getUserId(), member.getMemberRole());
    }

    @Transactional
    public TokenResponse register(RegisterRequest request) {
        if (memberRepository.existsByEmail(request.email())) {
            throw new BusinessException(ErrorCode.DUPLICATE_VALUE);
        }
        Member member = Member.builder()
                .email(request.email())
                .password(passwordEncoder.encode(request.password()))
                .nickname(request.nickname())
                .birthDate(request.birthDate())
                .memberStatus(MemberStatus.ACTIVE)
                .memberRole(MemberRole.ROLE_USER)
                .build();
        memberRepository.save(member);
        return issueToken(member.getUserId(), member.getMemberRole());
    }

    @Transactional
    public void logout(String accessToken) {
        try {
            authTokenProvider.validateToken(accessToken);
        } catch (Exception e) {
            return;
        }
        long remainingMs = authTokenProvider.getRemainingMs(accessToken);
        if (remainingMs > 0) {
            redisTemplate.opsForValue()
                    .set("auth:blacklist:" + accessToken, "logout", remainingMs, TimeUnit.MILLISECONDS);
        }
        redisTemplate.delete("auth:refresh:" + authTokenProvider.getSubject(accessToken));
    }

    @Transactional
    public TokenResponse reissue(String refreshToken) {
        try {
            authTokenProvider.validateToken(refreshToken);
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.INVALID_TOKEN);
        }

        long memberId = Long.parseLong(authTokenProvider.getSubject(refreshToken));
        String saved = redisTemplate.opsForValue().get("auth:refresh:" + memberId);
        if (saved == null || !saved.equals(refreshToken)) {
            throw new BusinessException(ErrorCode.INVALID_TOKEN);
        }

        redisTemplate.delete("auth:refresh:" + memberId);

        Member member = memberRepository.findById(memberId);
        if (member == null) {
            throw new BusinessException(ErrorCode.USER_NOT_FOUND);
        }
        return issueToken(memberId, member.getMemberRole());
    }

    private TokenResponse issueToken(Long memberId, MemberRole role) {
        Map<String, String> claims = Map.of("role", role.name());
        String accessToken = authTokenProvider.createAccessToken(memberId, claims);
        String refreshToken = authTokenProvider.createRefreshToken(memberId, claims);
        long expirationSeconds = authTokenProvider.getRefreshExpirationSeconds();

        try {
            redisTemplate.opsForValue()
                    .set("auth:refresh:" + memberId, refreshToken, expirationSeconds, TimeUnit.SECONDS);
        } catch (Exception e) {
            log.error("Redis error while storing refresh token for memberId={}", memberId, e);
            throw new BusinessException(ErrorCode.REDIS_ERROR);
        }
        return TokenResponse.of(accessToken, refreshToken, expirationSeconds);
    }
}
