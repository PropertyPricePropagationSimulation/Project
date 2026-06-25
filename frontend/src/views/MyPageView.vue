<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useAuthStore } from '@/stores/authStore'
import { useReportStore } from '@/stores/reportStore'
import { useScenarioStore } from '@/stores/scenarioStore'
import { getMember, parseUserId, updateMember, changePassword, withdrawMember, type MemberResponse } from '@/api/authApi'

const router = useRouter()
const authStore = useAuthStore()
const reportStore = useReportStore()
const scenarioStore = useScenarioStore()

const member = ref<MemberResponse | null>(null)
const loading = ref(false)

// 프로필 편집 모달
const showEditModal = ref(false)
const editNick = ref('')
const editBirthDate = ref('')
const editSaving = ref(false)
const editError = ref('')

// 비밀번호 변경 모달
const showPwModal = ref(false)
const pwCur = ref('')
const pwNew = ref('')
const pwConfirm = ref('')
const pwSaving = ref(false)
const pwError = ref('')
const pwSuccess = ref(false)

// 탈퇴 모달
const showWithdrawModal = ref(false)
const withdrawing = ref(false)

const totalReportPages = computed(() =>
  Math.max(1, Math.ceil(reportStore.reportTotalCount / reportStore.reportPageSize)),
)

onMounted(async () => {
  if (!authStore.isLoggedIn || !authStore.accessToken) {
    router.push('/login')
    return
  }

  loading.value = true
  try {
    const userId = parseUserId(authStore.accessToken)
    if (userId) {
      member.value = await getMember(userId, authStore.accessToken)
    }
    await reportStore.fetchMyReports()
  } finally {
    loading.value = false
  }
})

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

function openEditModal() {
  editNick.value = member.value?.nickname ?? authStore.nickname ?? ''
  editBirthDate.value = member.value?.birthDate ?? ''
  editError.value = ''
  showEditModal.value = true
}

async function saveProfile() {
  const trimmed = editNick.value.trim()
  if (!trimmed || trimmed.length < 2) { editError.value = '닉네임은 2자 이상이어야 합니다.'; return }
  if (trimmed.length > 20) { editError.value = '닉네임은 20자 이하여야 합니다.'; return }

  editSaving.value = true
  editError.value = ''
  try {
    const userId = member.value?.userId ?? parseUserId(authStore.accessToken ?? '')
    if (!userId) return
    await updateMember(userId, { nickname: trimmed, birthDate: editBirthDate.value || null })
    localStorage.setItem('nickname', trimmed)
    authStore.nickname = trimmed
    if (member.value) member.value = { ...member.value, nickname: trimmed, birthDate: editBirthDate.value || null }
    showEditModal.value = false
  } catch {
    editError.value = '프로필 수정에 실패했습니다.'
  } finally {
    editSaving.value = false
  }
}

function openPwModal() {
  pwCur.value = ''; pwNew.value = ''; pwConfirm.value = ''
  pwError.value = ''; pwSuccess.value = false
  showPwModal.value = true
}

async function savePassword() {
  if (!pwCur.value || !pwNew.value || !pwConfirm.value) { pwError.value = '모든 항목을 입력해주세요.'; return }
  if (pwNew.value.length < 8) { pwError.value = '새 비밀번호는 8자 이상이어야 합니다.'; return }
  if (pwNew.value !== pwConfirm.value) { pwError.value = '새 비밀번호가 일치하지 않습니다.'; return }

  pwSaving.value = true
  pwError.value = ''
  try {
    const userId = member.value?.userId ?? parseUserId(authStore.accessToken ?? '')
    if (!userId) return
    await changePassword(userId, pwCur.value, pwNew.value, pwConfirm.value)
    pwSuccess.value = true
  } catch {
    pwError.value = '비밀번호 변경에 실패했습니다. 현재 비밀번호를 확인해주세요.'
  } finally {
    pwSaving.value = false
  }
}

async function handleWithdraw() {
  withdrawing.value = true
  try {
    const userId = member.value?.userId ?? parseUserId(authStore.accessToken ?? '')
    if (!userId) return
    await withdrawMember(userId)
    await authStore.logout()
    router.push('/')
  } catch {
    showWithdrawModal.value = false
  } finally {
    withdrawing.value = false
  }
}

async function handlePersonaAnalysis(analysisCacheId: number) {
  const scenario = await scenarioStore.createFromAnalysisCache(analysisCacheId)
  if (scenario) router.push(`/scenarios/${scenario.scenario_id}`)
}

async function handleReportDelete(reportId: string) {
  if (!window.confirm('이 리포트를 목록에서 삭제할까요?')) return
  await reportStore.remove(reportId)
}

function fmtDate(value: string) {
  return value?.slice(0, 10) ?? ''
}
</script>

<template>
  <div class="mp">
    <AppHeader />

    <main class="mp-main">
      <div class="mp-inner">
        <section class="mp-section">
          <h2 class="mp-section-title">프로필</h2>

          <div v-if="loading" class="mp-loading">불러오는 중...</div>
          <div v-else class="mp-profile-card">
            <div class="mp-avatar">{{ (authStore.nickname ?? '?')[0] }}</div>

            <div class="mp-profile-info">
              <div class="mp-nick-row">
                <span class="mp-nick">{{ authStore.nickname }}</span>
              </div>
              <div class="mp-email">{{ member?.email ?? '-' }}</div>
              <div v-if="member?.birthDate" class="mp-birthdate">{{ member.birthDate }}</div>
            </div>

            <div class="mp-profile-actions">
              <button class="mp-nick-edit-btn" @click="openEditModal">프로필 수정</button>
              <button class="mp-nick-edit-btn" @click="openPwModal">비밀번호 변경</button>
            </div>
          </div>

          <div class="mp-withdraw-row">
            <button class="mp-withdraw-btn" @click="showWithdrawModal = true">회원 탈퇴</button>
          </div>

          <!-- 프로필 편집 모달 -->
          <Transition name="mp-modal">
            <div v-if="showEditModal" class="mp-modal-overlay" @click.self="showEditModal = false">
              <div class="mp-modal">
                <h3 class="mp-modal-title">프로필 수정</h3>

                <div class="mp-form">
                  <label class="mp-form-label">이메일</label>
                  <input class="mp-form-input mp-form-input--readonly" :value="member?.email ?? ''" readonly />

                  <label class="mp-form-label">닉네임</label>
                  <input
                    v-model="editNick"
                    class="mp-form-input"
                    maxlength="20"
                    placeholder="2~20자"
                    @keyup.enter="saveProfile"
                  />

                  <label class="mp-form-label">생년월일</label>
                  <input
                    v-model="editBirthDate"
                    class="mp-form-input"
                    type="date"
                  />
                </div>

                <span v-if="editError" class="mp-form-err">{{ editError }}</span>

                <div class="mp-modal-actions">
                  <button class="mp-modal-cancel" @click="showEditModal = false">취소</button>
                  <button class="mp-modal-confirm mp-modal-confirm--save" :disabled="editSaving" @click="saveProfile">
                    {{ editSaving ? '저장 중...' : '저장' }}
                  </button>
                </div>
              </div>
            </div>
          </Transition>

          <!-- 비밀번호 변경 모달 -->
          <Transition name="mp-modal">
            <div v-if="showPwModal" class="mp-modal-overlay" @click.self="showPwModal = false">
              <div class="mp-modal">
                <h3 class="mp-modal-title">비밀번호 변경</h3>

                <div v-if="pwSuccess" class="mp-pw-success">비밀번호가 변경되었습니다.</div>
                <div v-else class="mp-form">
                  <label class="mp-form-label">현재 비밀번호</label>
                  <input v-model="pwCur" class="mp-form-input" type="password" @keyup.enter="savePassword" />

                  <label class="mp-form-label">새 비밀번호</label>
                  <input v-model="pwNew" class="mp-form-input" type="password" placeholder="8자 이상" @keyup.enter="savePassword" />

                  <label class="mp-form-label">새 비밀번호 확인</label>
                  <input v-model="pwConfirm" class="mp-form-input" type="password" @keyup.enter="savePassword" />
                </div>

                <span v-if="pwError" class="mp-form-err">{{ pwError }}</span>

                <div class="mp-modal-actions">
                  <template v-if="pwSuccess">
                    <button class="mp-modal-confirm mp-modal-confirm--save" @click="showPwModal = false">확인</button>
                  </template>
                  <template v-else>
                    <button class="mp-modal-cancel" @click="showPwModal = false">취소</button>
                    <button class="mp-modal-confirm mp-modal-confirm--save" :disabled="pwSaving" @click="savePassword">
                      {{ pwSaving ? '변경 중...' : '변경' }}
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </Transition>
        </section>

        <div v-if="showWithdrawModal" class="mp-modal-overlay" @click.self="showWithdrawModal = false">
          <div class="mp-modal">
            <h3 class="mp-modal-title">정말 탈퇴하시겠습니까?</h3>
            <p class="mp-modal-desc">
              탈퇴 후에는 다시 로그인할 수 없으며, 작성한 데이터는 서비스 운영 정책에 따라 처리됩니다.
            </p>
            <div class="mp-modal-actions">
              <button class="mp-modal-cancel" @click="showWithdrawModal = false">취소</button>
              <button class="mp-modal-confirm" :disabled="withdrawing" @click="handleWithdraw">
                {{ withdrawing ? '처리 중...' : '탈퇴하기' }}
              </button>
            </div>
          </div>
        </div>

        <section class="mp-section">
          <div class="mp-section-hdr">
            <h2 class="mp-section-title">AI 리포트</h2>
            <button class="mp-refresh-btn" :disabled="reportStore.listLoading" @click="reportStore.fetchMyReports()">
              새로고침
            </button>
          </div>

          <div v-if="reportStore.listLoading" class="mp-loading">리포트를 불러오는 중입니다...</div>

          <div v-else-if="reportStore.reports.length > 0" class="mp-report-list">
            <article v-for="item in reportStore.reports" :key="item.report_id" class="mp-report-card">
              <div class="mp-report-head">
                <div>
                  <span class="mp-report-kicker">AI REPORT</span>
                  <p class="mp-report-title">{{ item.title }}</p>
                </div>
                <button
                  class="mp-delete-btn mp-delete-btn-sm"
                  :disabled="reportStore.loading"
                  @click="handleReportDelete(item.report_id)"
                >
                  삭제
                </button>
              </div>

              <div class="mp-report-meta">
                생성일 {{ fmtDate(item.created_at) }} · 분석 캐시 #{{ item.analysis_cache_id }}
              </div>

              <div class="mp-report-actions">
                <button
                  class="mp-persona-btn"
                  :disabled="scenarioStore.loading"
                  @click="handlePersonaAnalysis(item.analysis_cache_id)"
                >
                  {{ scenarioStore.loading ? '분석 준비 중...' : '시장 참여자 분석' }}
                </button>
                <button
                  class="mp-download-btn"
                  :disabled="reportStore.loading"
                  @click="reportStore.download(item.report_id)"
                >
                  {{ reportStore.loading ? 'PDF 준비 중...' : 'PDF 다운로드' }}
                </button>
              </div>
            </article>

            <p v-if="scenarioStore.error" class="mp-scenario-hint err">{{ scenarioStore.error }}</p>

            <div v-if="totalReportPages > 1" class="mp-report-pagination">
              <button
                class="mp-page-btn"
                :disabled="reportStore.reportPage <= 1 || reportStore.listLoading"
                @click="reportStore.fetchMyReports(reportStore.reportPage - 1)"
              >
                이전
              </button>
              <span class="mp-page-state">
                {{ reportStore.reportPage }} / {{ totalReportPages }}
              </span>
              <button
                class="mp-page-btn"
                :disabled="reportStore.reportPage >= totalReportPages || reportStore.listLoading"
                @click="reportStore.fetchMyReports(reportStore.reportPage + 1)"
              >
                다음
              </button>
            </div>
          </div>

          <div v-else class="mp-report-empty">
            <div class="mp-empty-icon">REPORT</div>
            <p>생성된 리포트가 없습니다.</p>
            <p class="mp-empty-sub">분석 페이지에서 이벤트를 선택하고 AI 리포트를 먼저 생성해 주세요.</p>
            <router-link to="/analysis" class="mp-go-analysis">분석 시작하기</router-link>
          </div>

          <p v-if="reportStore.listError" class="mp-scenario-hint err">{{ reportStore.listError }}</p>
          <p v-if="reportStore.error" class="mp-scenario-hint err">{{ reportStore.error }}</p>
        </section>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.mp { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }
.mp-main { flex: 1; padding: 40px 24px; }
.mp-inner { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
.mp-section { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; }
.mp-section-title { font-size: 16px; font-weight: 700; color: #1e293b; padding: 24px 28px 0; }
.mp-section-hdr { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 28px; }
.mp-section-hdr .mp-section-title { padding: 24px 0 0; }
.mp-loading { padding: 28px; color: #64748b; font-size: 14px; }
.mp-profile-card { display: flex; align-items: center; gap: 16px; padding: 28px; }
.mp-avatar { width: 52px; height: 52px; border-radius: 50%; background: #1e293b; color: #fff; font-size: 20px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mp-profile-info { flex: 1; min-width: 0; }
.mp-nick-row { display: flex; align-items: center; gap: 8px; }
.mp-birthdate { font-size: 13px; color: #94a3b8; margin-top: 2px; }
.mp-profile-actions { display: flex; flex-direction: column; gap: 6px; margin-left: auto; }
.mp-nick-edit-btn {
  padding: 5px 12px;
  border: 1px solid #e2e8f0;
  background: none;
  color: #64748b;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all .12s;
  font-family: inherit;
  white-space: nowrap;
}
.mp-nick-edit-btn:hover { border-color: #cbd5e1; color: #1e293b; }

/* 폼 */
.mp-form { display: flex; flex-direction: column; gap: 6px; margin-bottom: 4px; }
.mp-form-label { font-size: 12px; font-weight: 600; color: #64748b; margin-top: 8px; }
.mp-form-input {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #1e293b;
  font-family: inherit;
  transition: border-color .12s;
}
.mp-form-input:focus { outline: none; border-color: #94a3b8; }
.mp-form-input--readonly { background: #f8fafc; color: #94a3b8; cursor: default; }
.mp-form-err { font-size: 12px; color: #ef4444; display: block; margin-bottom: 8px; }
.mp-pw-success { text-align: center; padding: 24px 0; font-size: 15px; font-weight: 600; color: #16a34a; }
.mp-modal-confirm--save { background: #1e293b; }
.mp-modal-confirm--save:hover:not(:disabled) { background: #334155; }

/* 모달 트랜지션 */
.mp-modal-enter-active, .mp-modal-leave-active { transition: opacity .15s; }
.mp-modal-enter-from, .mp-modal-leave-to { opacity: 0; }
.mp-modal-enter-active .mp-modal, .mp-modal-leave-active .mp-modal { transition: transform .15s; }
.mp-modal-enter-from .mp-modal, .mp-modal-leave-to .mp-modal { transform: scale(0.96) translateY(-6px); }
.mp-withdraw-row { padding: 12px 28px 20px; border-top: 1px solid #f1f5f9; }
.mp-withdraw-btn { background: none; border: 0; color: #94a3b8; font-size: 12px; cursor: pointer; text-decoration: underline; font-family: inherit; }
.mp-withdraw-btn:hover { color: #dc2626; }
.mp-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px; }
.mp-modal { background: #fff; border-radius: 14px; padding: 28px; width: min(400px, 100%); box-shadow: 0 20px 60px rgba(0,0,0,.15); }
.mp-modal-title { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }
.mp-modal-desc { font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 24px; }
.mp-modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.mp-modal-cancel,
.mp-modal-confirm { padding: 9px 18px; border-radius: 8px; font-size: 14px; cursor: pointer; font-family: inherit; }
.mp-modal-cancel { background: #fff; border: 1px solid #e2e8f0; color: #64748b; }
.mp-modal-confirm { background: #dc2626; color: #fff; border: 0; font-weight: 600; }
.mp-modal-confirm:disabled { opacity: .5; cursor: not-allowed; }
.mp-report-list { display: grid; gap: 12px; padding: 24px 28px 28px; }
.mp-report-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; background: #fff; }
.mp-report-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.mp-report-kicker { display: block; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: #2563eb; margin-bottom: 4px; }
.mp-report-title { font-size: 16px; font-weight: 700; color: #1e293b; line-height: 1.45; word-break: keep-all; }
.mp-report-meta { font-size: 12px; color: #94a3b8; margin-bottom: 14px; }
.mp-report-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mp-download-btn,
.mp-persona-btn,
.mp-delete-btn { width: 100%; padding: 10px; border: 0; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; transition: background .15s; font-family: inherit; }
.mp-download-btn { background: #1e293b; color: #fff; }
.mp-download-btn:hover:not(:disabled) { background: #334155; }
.mp-persona-btn { background: #2563eb; color: #fff; }
.mp-persona-btn:hover:not(:disabled) { background: #1d4ed8; }
.mp-delete-btn { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }
.mp-delete-btn:hover:not(:disabled) { background: #ffe4e6; border-color: #fda4af; }
.mp-delete-btn-sm { width: auto; padding: 5px 10px; border-radius: 999px; font-size: 12px; white-space: nowrap; flex-shrink: 0; }
.mp-download-btn:disabled,
.mp-persona-btn:disabled,
.mp-delete-btn:disabled { opacity: .5; cursor: not-allowed; }
.mp-report-pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding-top: 6px; }
.mp-page-btn { border: 1px solid #e2e8f0; background: #fff; color: #475569; border-radius: 7px; cursor: pointer; font-family: inherit; font-size: 13px; font-weight: 700; padding: 7px 13px; }
.mp-page-btn:hover:not(:disabled) { border-color: #cbd5e1; color: #1e293b; }
.mp-page-btn:disabled { cursor: not-allowed; opacity: .45; }
.mp-page-state { color: #64748b; font-size: 13px; font-weight: 700; min-width: 54px; text-align: center; }
.mp-scenario-hint { margin: 0 28px 20px; font-size: 12px; color: #64748b; }
.mp-scenario-hint.err { color: #dc2626; }
.mp-report-empty { padding: 52px 28px; text-align: center; }
.mp-empty-icon { display: inline-flex; align-items: center; justify-content: center; height: 34px; padding: 0 12px; border-radius: 999px; background: #eff6ff; color: #2563eb; font-size: 11px; font-weight: 800; letter-spacing: .12em; margin-bottom: 14px; }
.mp-report-empty p { font-size: 15px; color: #475569; font-weight: 600; }
.mp-empty-sub { font-size: 13px; color: #94a3b8; margin-top: 6px; font-weight: 400; }
.mp-go-analysis { display: inline-block; margin-top: 20px; padding: 10px 24px; background: #1e293b; color: #fff; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 700; transition: background .15s; }
.mp-go-analysis:hover { background: #334155; }

@media (max-width: 720px) {
  .mp-main { padding: 24px 14px; }
  .mp-profile-card { align-items: flex-start; }
  .mp-report-actions { grid-template-columns: 1fr; }
}
</style>
