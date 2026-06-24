package com.example.home.domain.scenario.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
public class ScenarioPromptLoader {

    private static final String SYSTEM_PROMPT_PATH = "prompts/scenario/round-explanation-system.md";
    private static final String OUTPUT_SCHEMA_PATH = "prompts/scenario/round-explanation-output-schema.json";

    private final String systemPrompt;
    private final String outputSchema;
    private final String version;

    public ScenarioPromptLoader() {
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
            throw new IllegalStateException("시나리오 프롬프트 파일을 읽지 못했습니다. " + path, e);
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
