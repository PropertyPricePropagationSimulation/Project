package com.example.home.domain.report.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
public class ReportPromptLoader {

    private static final String SYSTEM_PROMPT_PATH = "prompts/report/report-enhancement-system.md";
    private static final String OUTPUT_SCHEMA_PATH = "prompts/report/report-output-schema.json";

    private final String systemPrompt;
    private final String outputSchema;
    private final String version;

    public ReportPromptLoader() {
        this.systemPrompt = read(SYSTEM_PROMPT_PATH);
        this.outputSchema = read(OUTPUT_SCHEMA_PATH);
        this.version = extractVersion(systemPrompt);
    }

    public String systemPrompt() {
        return systemPrompt;
    }

    public String outputSchema() {
        return outputSchema;
    }

    public String version() {
        return version;
    }

    private String read(String path) {
        try {
            return new ClassPathResource(path).getContentAsString(StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("리포트 프롬프트 파일을 읽지 못했습니다: " + path, e);
        }
    }

    private String extractVersion(String prompt) {
        return prompt.lines()
                .filter(line -> line.startsWith("Prompt-Version:"))
                .map(line -> line.substring("Prompt-Version:".length()).trim())
                .findFirst()
                .orElse("unknown");
    }
}
