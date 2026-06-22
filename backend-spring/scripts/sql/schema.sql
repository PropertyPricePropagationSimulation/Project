-- EstateFlow 전체 스키마
-- 초기 세팅 시 실행 (기존 DB가 없는 경우)
-- 실행: mysql -u root -p estateflow < scripts/sql/schema.sql

CREATE DATABASE IF NOT EXISTS estateflow
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE estateflow;

-- =============================================
-- member
-- =============================================
CREATE TABLE IF NOT EXISTS member (
    user_id       BIGINT       NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL,
    password      VARCHAR(255) NOT NULL,
    nickname      VARCHAR(50)  NOT NULL,
    birth_date    DATE         NOT NULL,
    member_status VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    member_role   VARCHAR(20)  NOT NULL DEFAULT 'ROLE_USER',
    created_at    DATETIME     NOT NULL DEFAULT NOW(),
    updated_at    DATETIME     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_member_email (email)
);

-- =============================================
-- notice
-- =============================================
CREATE TABLE IF NOT EXISTS notice (
    notice_id  BIGINT       NOT NULL AUTO_INCREMENT,
    title      VARCHAR(255) NOT NULL,
    writer_id  BIGINT       NOT NULL,
    writer     VARCHAR(50)  NOT NULL,
    content    TEXT         NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT NOW(),
    updated_at DATETIME     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (notice_id),
    CONSTRAINT fk_notice_member FOREIGN KEY (writer_id) REFERENCES member (user_id)
);

-- =============================================
-- qna
-- =============================================
CREATE TABLE IF NOT EXISTS qna (
    qna_id     BIGINT       NOT NULL AUTO_INCREMENT,
    title      VARCHAR(255) NOT NULL,
    writer_id  BIGINT       NOT NULL,
    writer     VARCHAR(50)  NOT NULL,
    content    TEXT         NOT NULL,
    answered   TINYINT(1)   NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT NOW(),
    updated_at DATETIME     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (qna_id),
    CONSTRAINT fk_qna_member FOREIGN KEY (writer_id) REFERENCES member (user_id)
);

-- =============================================
-- qna_comment
-- =============================================
CREATE TABLE IF NOT EXISTS qna_comment (
    comment_id BIGINT       NOT NULL AUTO_INCREMENT,
    qna_id     BIGINT       NOT NULL,
    content    TEXT         NOT NULL,
    writer     VARCHAR(50)  NOT NULL,
    writer_id  BIGINT       NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT NOW(),
    updated_at DATETIME     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (comment_id),
    CONSTRAINT fk_qna_comment_qna    FOREIGN KEY (qna_id)    REFERENCES qna    (qna_id)    ON DELETE CASCADE,
    CONSTRAINT fk_qna_comment_member FOREIGN KEY (writer_id) REFERENCES member (user_id)
);
