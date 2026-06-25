# ── 빌드 스테이지 ────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /build

# 의존성 레이어 캐시 (pom.xml만 먼저 복사)
COPY backend/pom.xml .
RUN mvn dependency:go-offline -q

# 소스 빌드
COPY backend/src ./src
RUN mvn package -DskipTests -q

# ── 실행 스테이지 ────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-jammy

# 한글 폰트 설치 (PDF 생성에 필요)
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=build /build/target/*.jar app.jar
COPY backend/seed ./seed

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
