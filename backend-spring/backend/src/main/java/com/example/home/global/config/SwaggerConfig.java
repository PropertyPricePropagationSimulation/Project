package com.example.home.global.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(info = @Info(title = "EstateFlow API", description = "부동산 정책 충격 전파 분석 시스템 API", version = "v1"))
@SecurityScheme(
        name = "bearerAuth",
        type = SecuritySchemeType.HTTP,
        scheme = "bearer",
        bearerFormat = "JWT"
)
public class SwaggerConfig {

    @Bean
    GroupedOpenApi authOpenApi() {
        return GroupedOpenApi.builder()
                .group("Auth 관련 API")
                .pathsToMatch("/api/auth/**")
                .build();
    }

    @Bean
    GroupedOpenApi memberOpenAPI() {
        return GroupedOpenApi.builder()
                .group("Member 관련 API")
                .pathsToMatch("/api/members/**")
                .build();
    }

    @Bean
    GroupedOpenApi qnaOpenAPI() {
        return GroupedOpenApi.builder()
                .group("Qna 관련 API")
                .pathsToMatch("/api/qnas/**")
                .build();
    }

    @Bean
    GroupedOpenApi noticeOpenAPI() {
        return GroupedOpenApi.builder()
                .group("Notice 관련 API")
                .pathsToMatch("/api/notices/**")
                .build();
    }
    
    @Bean
    GroupedOpenApi analysisOpenAPI() {
        return GroupedOpenApi.builder()
                .group("Analysis 관련 API")
                .pathsToMatch("/api/analysis/**")
                .build();
    }

    @Bean
    GroupedOpenApi reportOpenAPI() {
        return GroupedOpenApi.builder()
                .group("Report 관련 API")
                .pathsToMatch("/api/reports/**")
                .build();
    }
}
