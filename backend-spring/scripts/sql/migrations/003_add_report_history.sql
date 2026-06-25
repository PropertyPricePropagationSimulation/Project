CREATE TABLE IF NOT EXISTS report_history (
    report_id         VARCHAR(36)  NOT NULL,
    user_id           BIGINT       NOT NULL,
    analysis_cache_id BIGINT       NOT NULL,
    title             VARCHAR(255) NOT NULL,
    status            VARCHAR(30)  NOT NULL,
    created_at        DATETIME     NOT NULL DEFAULT NOW(),
    updated_at        DATETIME     NOT NULL DEFAULT NOW(),

    PRIMARY KEY (report_id),
    UNIQUE KEY uk_report_history_user_cache (user_id, analysis_cache_id),
    KEY idx_report_history_user_created (user_id, created_at),
    KEY idx_report_history_cache (analysis_cache_id),

    CONSTRAINT fk_report_history_member
        FOREIGN KEY (user_id) REFERENCES member (user_id),

    CONSTRAINT fk_report_history_analysis_cache
        FOREIGN KEY (analysis_cache_id) REFERENCES analysis_cache (cache_id)
);
