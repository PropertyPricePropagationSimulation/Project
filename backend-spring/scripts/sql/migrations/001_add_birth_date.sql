-- Migration 001: member 테이블에 birth_date 컬럼 추가
-- 실행 대상: 이미 member 테이블이 존재하는 기존 DB
-- 실행: mysql -u root -p estateflow < scripts/sql/migrations/001_add_birth_date.sql

USE estateflow;

-- Step 1: NULL 허용으로 컬럼 추가 (기존 데이터 보호)
ALTER TABLE member
    ADD COLUMN birth_date DATE AFTER nickname;

-- Step 2: 기존 데이터가 있다면 아래 주석을 해제하고 적절한 날짜로 채운 뒤 실행
-- UPDATE member SET birth_date = '1990-01-01' WHERE birth_date IS NULL;

-- Step 3: NOT NULL 제약 적용 (Step 2 완료 후 실행)
ALTER TABLE member
    MODIFY COLUMN birth_date DATE NOT NULL;
