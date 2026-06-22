package com.example.home.domain.auth.provider;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collection;
import java.util.Date;
import java.util.Map;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.stereotype.Component;

@Component
public class AuthTokenProvider {

    @Value("${custom.jwt.secret-key}")
    private String secret;

    @Value("${custom.jwt.access-expire-seconds}")
    private Long jwtAccessExpirationSeconds;

    @Value("${custom.jwt.refresh-expire-seconds}")
    private Long jwtRefreshExpirationSeconds;

    private SecretKey secretKey;

    @PostConstruct
    private void init() {
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    private String buildToken(String subject, long expireSeconds, Map<String, String> claims) {
        Date issuedAt = new Date();
        Date expiration = new Date(issuedAt.getTime() + 1000L * expireSeconds);
        return Jwts.builder()
                .claims(claims)
                .subject(subject)
                .issuedAt(issuedAt)
                .expiration(expiration)
                .signWith(secretKey)
                .compact();
    }

    public String createAccessToken(Long id, Map<String, String> claims) {
        return buildToken(String.valueOf(id), jwtAccessExpirationSeconds, claims);
    }

    public String createRefreshToken(Long id, Map<String, String> claims) {
        return buildToken(String.valueOf(id), jwtRefreshExpirationSeconds, claims);
    }

    // parseSignedClaims: 서명 검증 + 만료 확인을 동시에 수행. 실패 시 JwtException 발생.
    public void validateToken(String token) {
        Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token);
    }

    public Claims getClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public String getSubject(String token) {
        return getClaims(token).getSubject();
    }

    public Long getRemainingMs(String token) {
        return getClaims(token).getExpiration().getTime() - System.currentTimeMillis();
    }

    public Long getRefreshExpirationSeconds() {
        return jwtRefreshExpirationSeconds;
    }

    public Authentication getAuthentication(String token) {
        Claims claims = getClaims(token);
        Collection<? extends GrantedAuthority> authorities =
                Arrays.stream(claims.get("role").toString().split(","))
                        .map(SimpleGrantedAuthority::new)
                        .toList();
        User principal = new User(claims.getSubject(), "", authorities);
        return new UsernamePasswordAuthenticationToken(principal, "", authorities);
    }
}
