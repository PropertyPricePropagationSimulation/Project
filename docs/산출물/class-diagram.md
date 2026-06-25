# EstateFlow 전체 클래스 다이어그램

이 문서는 EstateFlow의 주요 Spring Boot 백엔드 구조를 기준으로 작성한 클래스 다이어그램입니다.  
전체 흐름을 한 번에 파악할 수 있도록 `Controller - Service - Repository/Client - Entity/DTO` 관계를 중심으로 정리했습니다.

## 1. 전체 도메인 관계도

```mermaid
classDiagram
direction LR

class EstateFlowApplication {
  +main(args)
}

class SecurityConfig
class JwtAuthenticationFilter
class AuthTokenProvider
class SecurityUtils
class BaseTimeEntity {
  <<abstract>>
  +createdAt
  +updatedAt
}

class AuthController
class AuthService
class MemberController
class MemberService {
  <<interface>>
}
class DefaultMemberService
class MemberRepository {
  <<interface>>
}
class Member
class MemberRole {
  <<enum>>
}
class MemberStatus {
  <<enum>>
}

class AnalysisController
class AnalysisService {
  <<interface>>
}
class DefaultAnalysisService
class AiServerClient
class AnalysisCacheRepository {
  <<interface>>
}
class AnalysisCache
class AnalysisCacheKey

class DealController
class DealService {
  <<interface>>
}
class DefaultDealService
class MolitApiClient

class NoticeController
class NoticeService {
  <<interface>>
}
class DefaultNoticeService
class NoticeRepository {
  <<interface>>
}
class Notice

class QnaController
class QnaCommentController
class QnaService {
  <<interface>>
}
class QnaCommentService {
  <<interface>>
}
class DefaultQnaService
class DefaultQnaCommentService
class QnaRepository {
  <<interface>>
}
class QnaCommentRepository {
  <<interface>>
}
class Qna
class QnaComment

class ReportController
class ReportService {
  <<interface>>
}
class DefaultReportService
class ReportAiService
class ReportPdfService
class ReportDraftGenerator
class ReportPromptLoader
class ReportValidationService
class ReportSeedStore
class ReportHistoryRepository {
  <<interface>>
}
class ReportHistory

class ScenarioController
class ScenarioService {
  <<interface>>
}
class DefaultScenarioService
class ScenarioSimulationService
class ScenarioAiExplanationService
class ScenarioPromptLoader
class ScenarioSeedStore
class AgentStance {
  <<enum>>
}
class PersonaType {
  <<enum>>
}

EstateFlowApplication ..> SecurityConfig
SecurityConfig --> JwtAuthenticationFilter
JwtAuthenticationFilter --> AuthTokenProvider

AuthController --> AuthService
AuthService --> MemberRepository
AuthService --> AuthTokenProvider
AuthService --> Member

MemberController --> MemberService
DefaultMemberService ..|> MemberService
DefaultMemberService --> MemberRepository
MemberRepository --> Member
Member --|> BaseTimeEntity
Member --> MemberRole
Member --> MemberStatus

AnalysisController --> AnalysisService
DefaultAnalysisService ..|> AnalysisService
DefaultAnalysisService --> AiServerClient
DefaultAnalysisService --> AnalysisCacheRepository
DefaultAnalysisService --> AnalysisCacheKey
AnalysisCacheRepository --> AnalysisCache

DealController --> DealService
DefaultDealService ..|> DealService
DefaultDealService --> MolitApiClient

NoticeController --> NoticeService
DefaultNoticeService ..|> NoticeService
DefaultNoticeService --> NoticeRepository
NoticeRepository --> Notice
Notice --|> BaseTimeEntity

QnaController --> QnaService
QnaCommentController --> QnaCommentService
DefaultQnaService ..|> QnaService
DefaultQnaService --> QnaRepository
DefaultQnaService --> Qna
DefaultQnaCommentService ..|> QnaCommentService
DefaultQnaCommentService --> QnaCommentRepository
DefaultQnaCommentService --> QnaRepository
QnaRepository --> Qna
QnaCommentRepository --> QnaComment
Qna --|> BaseTimeEntity
QnaComment --|> BaseTimeEntity
Qna "1" --> "0..*" QnaComment

ReportController --> ReportService
ReportController --> ReportPdfService
DefaultReportService ..|> ReportService
DefaultReportService --> AnalysisCacheRepository
DefaultReportService --> ReportDraftGenerator
DefaultReportService --> ReportAiService
DefaultReportService --> ReportSeedStore
DefaultReportService --> ReportHistoryRepository
ReportAiService --> ReportPromptLoader
ReportAiService --> ReportValidationService
ReportHistoryRepository --> ReportHistory

ScenarioController --> ScenarioService
DefaultScenarioService ..|> ScenarioService
DefaultScenarioService --> AnalysisService
DefaultScenarioService --> AnalysisCacheRepository
DefaultScenarioService --> ScenarioSimulationService
DefaultScenarioService --> ScenarioAiExplanationService
DefaultScenarioService --> ScenarioSeedStore
ScenarioAiExplanationService --> ScenarioPromptLoader
ScenarioSimulationService --> AgentStance
ScenarioSimulationService --> PersonaType
```

## 2. 회원/인증 도메인

```mermaid
classDiagram
direction LR

class AuthController {
  +login(LoginRequest)
  +register(RegisterRequest)
  +refresh(refreshToken)
  +logout()
}
class AuthService {
  +login(LoginRequest) TokenResponse
  +register(RegisterRequest) TokenResponse
  +logout(accessToken)
  +reissue(refreshToken) TokenResponse
}
class AuthTokenProvider {
  +createAccessToken(id, claims) String
  +createRefreshToken(id, claims) String
  +validateToken(token)
  +getAuthentication(token) Authentication
}
class JwtAuthenticationFilter {
  +doFilter(request, response, chain)
}
class MemberController {
  +getMember(id)
  +updateMember(id, request)
  +changePassword(id, request)
}
class MemberService {
  <<interface>>
}
class DefaultMemberService
class MemberRepository {
  <<interface>>
  +findByEmail(email)
  +findById(id)
  +save(member)
}
class Member {
  +userId
  +email
  +password
  +nickname
  +birthDate
  +memberStatus
  +memberRole
}
class LoginRequest {
  <<record>>
  +email
  +password
}
class RegisterRequest {
  <<record>>
  +email
  +password
  +nickname
  +birthDate
}
class TokenResponse {
  <<record>>
  +accessToken
  +refreshToken
  +expiresIn
}
class MemberRole {
  <<enum>>
  USER
  ADMIN
}
class MemberStatus {
  <<enum>>
  ACTIVE
  DELETED
}

AuthController --> AuthService
AuthController ..> LoginRequest
AuthController ..> RegisterRequest
AuthService --> AuthTokenProvider
AuthService --> MemberRepository
AuthService ..> TokenResponse
JwtAuthenticationFilter --> AuthTokenProvider
MemberController --> MemberService
DefaultMemberService ..|> MemberService
DefaultMemberService --> MemberRepository
MemberRepository --> Member
Member --> MemberRole
Member --> MemberStatus
```

## 3. 분석/거래 조회 도메인

```mermaid
classDiagram
direction LR

class AnalysisController {
  +events()
  +eventWindow(EventWindowRequest)
}
class AnalysisService {
  <<interface>>
  +analyze(EventWindowRequest) EventWindowResponse
  +getCachedResult(cacheId) EventWindowResponse
}
class DefaultAnalysisService
class AiServerClient {
  +getEvents()
  +postEventWindow(request)
}
class AnalysisCacheRepository {
  <<interface>>
  +findByKey(eventId, windowMonths, regionSignature)
  +findById(cacheId)
  +save(cache)
}
class AnalysisCache {
  +cacheId
  +eventId
  +windowMonths
  +regionSignature
  +resultJson
}
class AnalysisCacheKey {
  +regionSignature(regionCodes) String
}
class EventWindowRequest {
  <<record>>
  +eventId
  +windowMonths
  +regionCodes
}
class EventWindowResponse {
  <<record>>
  +analysisCacheId
  +event
  +summary
  +regions
  +rankings
}
class DealController {
  +getDeals(regionCode, yearMonth)
}
class DealService {
  <<interface>>
}
class DefaultDealService
class MolitApiClient {
  +getAptDeals(regionCode, yearMonth)
}
class AptDealResponse {
  <<record>>
}

AnalysisController --> AnalysisService
AnalysisController ..> EventWindowRequest
AnalysisService ..> EventWindowResponse
DefaultAnalysisService ..|> AnalysisService
DefaultAnalysisService --> AiServerClient
DefaultAnalysisService --> AnalysisCacheRepository
DefaultAnalysisService --> AnalysisCacheKey
AnalysisCacheRepository --> AnalysisCache

DealController --> DealService
DefaultDealService ..|> DealService
DefaultDealService --> MolitApiClient
MolitApiClient ..> AptDealResponse
```

## 4. 게시판 도메인

```mermaid
classDiagram
direction LR

class NoticeController {
  +getNotices(page, size)
  +getNotice(id)
  +createNotice(request)
  +updateNotice(id, request)
  +deleteNotice(id)
}
class NoticeService {
  <<interface>>
}
class DefaultNoticeService
class NoticeRepository {
  <<interface>>
}
class Notice {
  +noticeId
  +title
  +content
  +writerId
}
class NoticeRequest {
  <<record>>
  +title
  +content
}
class NoticeResponse {
  <<record>>
}

class QnaController {
  +getQnas(page, size)
  +getQna(id)
  +createQna(request)
  +updateQna(id, request)
  +deleteQna(id)
  +updateAnswered(id, request)
}
class QnaCommentController {
  +getComments(qnaId)
  +createComment(qnaId, request)
  +updateComment(qnaId, commentId, request)
  +deleteComment(qnaId, commentId)
}
class QnaService {
  <<interface>>
}
class QnaCommentService {
  <<interface>>
}
class DefaultQnaService
class DefaultQnaCommentService
class QnaRepository {
  <<interface>>
}
class QnaCommentRepository {
  <<interface>>
}
class Qna {
  +qnaId
  +title
  +content
  +writerId
  +answered
}
class QnaComment {
  +commentId
  +qnaId
  +content
  +writerId
}

NoticeController --> NoticeService
DefaultNoticeService ..|> NoticeService
DefaultNoticeService --> NoticeRepository
NoticeRepository --> Notice
NoticeController ..> NoticeRequest
NoticeController ..> NoticeResponse

QnaController --> QnaService
QnaCommentController --> QnaCommentService
DefaultQnaService ..|> QnaService
DefaultQnaCommentService ..|> QnaCommentService
DefaultQnaService --> QnaRepository
DefaultQnaCommentService --> QnaRepository
DefaultQnaCommentService --> QnaCommentRepository
QnaRepository --> Qna
QnaCommentRepository --> QnaComment
Qna "1" --> "0..*" QnaComment
```

## 5. AI 리포트 도메인

```mermaid
classDiagram
direction LR

class ReportController {
  +create(CreateReportRequest)
  +getMyReports(page, size)
  +get(reportId)
  +delete(reportId)
  +downloadPdf(reportId)
}
class ReportService {
  <<interface>>
  +create(userId, request) ReportDocument
  +get(reportId) ReportDocument
  +getMyReports(userId, page, size)
  +deleteMyReport(userId, reportId)
}
class DefaultReportService
class ReportDraftGenerator {
  +generate(analysisResult) ReportDraft
}
class ReportAiService {
  +enhance(ReportDraft, analysisResult) ReportAiResult
}
class ReportValidationService {
  +validateAiEnhancement(enhancement)
}
class ReportPromptLoader {
  +systemPrompt()
  +outputSchema()
  +version()
}
class ReportPdfService {
  +render(ReportDocument) byte[]
}
class ReportSeedStore {
  +save(ReportDocument)
  +get(reportId) ReportDocument
}
class ReportHistoryRepository {
  <<interface>>
}
class ReportHistory {
  +reportId
  +userId
  +analysisCacheId
  +title
  +status
  +deletedAt
}
class CreateReportRequest {
  <<record>>
  +eventId
  +windowMonths
  +regionCodes
}
class ReportDocument {
  <<record>>
  +reportId
  +status
  +createdAt
  +source
  +draft
  +aiEnhancement
  +generation
  +analysisResult
}
class ReportDraft {
  <<record>>
}
class ReportAiResult {
  <<record>>
  +status
  +promptVersion
  +model
  +enhancement
}
class ReportGeneration {
  <<record>>
}
class ReportSource {
  <<record>>
}

ReportController --> ReportService
ReportController --> ReportPdfService
DefaultReportService ..|> ReportService
DefaultReportService --> ReportDraftGenerator
DefaultReportService --> ReportAiService
DefaultReportService --> ReportSeedStore
DefaultReportService --> ReportHistoryRepository
DefaultReportService --> AnalysisCacheRepository
ReportAiService --> ReportPromptLoader
ReportAiService --> ReportValidationService
ReportPdfService --> ReportDocument
ReportHistoryRepository --> ReportHistory
ReportController ..> CreateReportRequest
DefaultReportService ..> ReportDocument
DefaultReportService ..> ReportDraft
DefaultReportService ..> ReportAiResult
ReportDocument --> ReportSource
ReportDocument --> ReportDraft
ReportDocument --> ReportGeneration
```

## 6. 시나리오 도메인

```mermaid
classDiagram
direction LR

class ScenarioController {
  +create(CreateScenarioRequest)
  +get(scenarioId)
  +explainRound(scenarioId, relativeMonth)
}
class ScenarioService {
  <<interface>>
  +create(request) ScenarioDocument
  +get(scenarioId) ScenarioDocument
  +explainRound(scenarioId, relativeMonth) ScenarioRoundExplanation
}
class DefaultScenarioService
class ScenarioSimulationService {
  +simulate(cacheId, eventId, windowMonths, regionCodes, agentsPerRegion, maxRegions, analysisResult) ScenarioDocument
}
class ScenarioAiExplanationService {
  +explain(document, round) ScenarioRoundExplanation
}
class ScenarioPromptLoader {
  +systemPrompt()
  +outputSchema()
}
class ScenarioSeedStore {
  +save(document)
  +get(scenarioId) ScenarioDocument
}
class CreateScenarioRequest {
  <<record>>
  +analysisCacheId
  +eventId
  +windowMonths
  +regionCodes
  +maxRegions
  +agentsPerRegion
}
class ScenarioDocument {
  <<record>>
  +scenarioId
  +source
  +selectedRegions
  +rounds
  +finalSummary
}
class ScenarioSource {
  <<record>>
}
class ScenarioRegionProfile {
  <<record>>
}
class ScenarioRound {
  <<record>>
  +relativeMonth
  +label
  +marketMood
  +regions
}
class ScenarioRoundRegion {
  <<record>>
}
class ScenarioPersonaSnapshot {
  <<record>>
}
class ScenarioFinalSummary {
  <<record>>
}
class ScenarioRoundExplanation {
  <<record>>
  +summary
  +regions
}
class ScenarioRoundExplanationRegion {
  <<record>>
  +regionCode
  +regionName
  +dominantStance
  +regionExplanation
  +personas
}
class ScenarioPersonaBehaviorExplanation {
  <<record>>
}
class AgentStance {
  <<enum>>
  BUY
  HOLD
  WATCH
  SELL
  MOVE
}
class PersonaType {
  <<enum>>
  INVESTOR
  END_USER
  MOVER
}

ScenarioController --> ScenarioService
DefaultScenarioService ..|> ScenarioService
DefaultScenarioService --> AnalysisService
DefaultScenarioService --> AnalysisCacheRepository
DefaultScenarioService --> ScenarioSimulationService
DefaultScenarioService --> ScenarioAiExplanationService
DefaultScenarioService --> ScenarioSeedStore
ScenarioAiExplanationService --> ScenarioPromptLoader
ScenarioController ..> CreateScenarioRequest
ScenarioSimulationService ..> ScenarioDocument
ScenarioSimulationService --> AgentStance
ScenarioSimulationService --> PersonaType
ScenarioDocument --> ScenarioSource
ScenarioDocument --> ScenarioRegionProfile
ScenarioDocument --> ScenarioRound
ScenarioDocument --> ScenarioFinalSummary
ScenarioRound --> ScenarioRoundRegion
ScenarioRoundRegion --> ScenarioPersonaSnapshot
ScenarioRoundExplanation --> ScenarioRoundExplanationRegion
ScenarioRoundExplanationRegion --> ScenarioPersonaBehaviorExplanation
```

## 7. 공통/예외 처리

```mermaid
classDiagram
direction LR

class BaseResponse~T~ {
  <<record>>
  +success
  +message
  +detail
}
class PageResponse~T~ {
  <<record>>
  +content
  +page
  +size
  +totalCount
  +totalPages
}
class BusinessException {
  +errorCode
  +message
}
class ErrorCode {
  <<enum>>
}
class GlobalExceptionHandler {
  +handleBusinessException()
  +handleValidationException()
  +handleException()
}
class SecurityUtils {
  +getCurrentUserId()
  +isAdmin()
}

BusinessException --> ErrorCode
GlobalExceptionHandler --> BusinessException
GlobalExceptionHandler --> BaseResponse
GlobalExceptionHandler --> ErrorCode
SecurityUtils ..> BusinessException
```
