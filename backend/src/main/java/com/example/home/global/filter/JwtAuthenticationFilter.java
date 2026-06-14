package com.example.home.global.filter;

import com.example.home.domain.auth.provider.AuthTokenProvider;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

// @Component 금지 - SecurityConfig의 FilterRegistrationBean으로만 등록 (이중 등록 방지)
@RequiredArgsConstructor
public class JwtAuthenticationFilter implements Filter {

    private final AuthTokenProvider authTokenProvider;
    private final RedisTemplate<String, String> redisTemplate;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        String token = extractToken((HttpServletRequest) request);

        if (token != null) {
            try {
                // getAuthentication 내부에서 parseSignedClaims 호출 → 서명 검증 + 만료 확인 한 번만 수행
                Authentication auth = authTokenProvider.getAuthentication(token);

                // 유효한 토큰일 때만 Redis 조회 (유효하지 않으면 위에서 예외 발생)
                Boolean blacklisted = redisTemplate.hasKey("auth:blacklist:" + token);
                if (Boolean.TRUE.equals(blacklisted)) {
                    chain.doFilter(request, response);
                    return;
                }

                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (Exception e) {
                SecurityContextHolder.clearContext();
            }
        }

        chain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }
}
