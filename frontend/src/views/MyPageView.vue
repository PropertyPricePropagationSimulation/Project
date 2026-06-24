<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useAuthStore } from '@/stores/authStore'
import { useReportStore } from '@/stores/reportStore'
import { getMember, parseUserId, updateMember, withdrawMember, type MemberResponse } from '@/api/authApi'

const router      = useRouter()
const authStore   = useAuthStore()
const reportStore = useReportStore()

const member  = ref<MemberResponse | null>(null)
const loading = ref(false)

const editingNick    = ref(false)
const newNick        = ref('')
const nickSaving     = ref(false)
const nickError      = ref('')
const showWithdrawModal = ref(false)
const withdrawing    = ref(false)

onMounted(async () => {
  if (!authStore.isLoggedIn || !authStore.accessToken) {
    router.push('/login')
    return
  }
  loading.value = true
  try {
    const userId = parseUserId(authStore.accessToken)
    if (userId) member.value = await getMember(userId, authStore.accessToken)
  } finally {
    loading.value = false
  }
})

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

function startEditNick() {
  newNick.value    = authStore.nickname ?? ''
  nickError.value  = ''
  editingNick.value = true
}

async function saveNick() {
  if (!newNick.value.trim() || newNick.value.trim().length < 2) {
    nickError.value = '닉네임은 2자 이상이어야 합니다.'
    return
  }
  if (newNick.value.trim().length > 20) {
    nickError.value = '닉네임은 20자 이하여야 합니다.'
    return
  }
  nickSaving.value = true
  nickError.value  = ''
  try {
    const userId = member.value?.userId ?? parseUserId(authStore.accessToken ?? '')
    if (!userId) return
    await updateMember(userId, newNick.value.trim())
    // 스토어 닉네임 갱신
    localStorage.setItem('nickname', newNick.value.trim())
    authStore.nickname = newNick.value.trim()
    if (member.value) member.value = { ...member.value, nickname: newNick.value.trim() }
    editingNick.value = false
  } catch {
    nickError.value = '닉네임 수정에 실패했습니다.'
  } finally {
    nickSaving.value = false
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

function fmtDate(s: string) { return s?.slice(0, 10) ?? '' }

function signed(v: number | undefined) {
  if (v === undefined) return '-'
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
</script>

<template>
  <div class="mp">
    <AppHeader />

    <main class="mp-main">
      <div class="mp-inner">

        <!-- 프로필 -->
        <section class="mp-section">
          <h2 class="mp-section-title">내 프로필</h2>
          <div v-if="loading" class="mp-loading">불러오는 중...</div>
          <div v-else class="mp-profile-card">
            <div class="mp-avatar">{{ (authStore.nickname ?? '?')[0] }}</div>
            <div class="mp-profile-info">
              <div v-if="editingNick" class="mp-nick-edit">
                <input v-model="newNick" class="mp-nick-input" maxlength="20"
                       @keyup.enter="saveNick" @keyup.esc="editingNick = false" />
                <div class="mp-nick-btns">
                  <button class="mp-nick-save" :disabled="nickSaving" @click="saveNick">
                    {{ nickSaving ? '저장 중...' : '저장' }}
                  </button>
                  <button class="mp-nick-cancel" @click="editingNick = false">취소</button>
                </div>
                <span v-if="nickError" class="mp-nick-err">{{ nickError }}</span>
              </div>
              <template v-else>
                <div class="mp-nick-row">
                  <span class="mp-nick">{{ authStore.nickname }}</span>
                  <button class="mp-nick-edit-btn" @click="startEditNick">수정</button>
                </div>
                <div class="mp-email">{{ member?.email ?? '-' }}</div>
              </template>
            </div>
            <button class="mp-logout" @click="handleLogout">로그아웃</button>
          </div>
          <div class="mp-withdraw-row">
            <button class="mp-withdraw-btn" @click="showWithdrawModal = true">회원 탈퇴</button>
          </div>
        </section>

        <!-- 탈퇴 확인 모달 -->
        <div v-if="showWithdrawModal" class="mp-modal-overlay" @click.self="showWithdrawModal = false">
          <div class="mp-modal">
            <h3 class="mp-modal-title">정말 탈퇴하시겠습니까?</h3>
            <p class="mp-modal-desc">탈퇴 후에는 로그인이 불가하며, 작성하신 게시글의 닉네임은 탈퇴 전 닉네임으로 유지됩니다.</p>
            <div class="mp-modal-actions">
              <button class="mp-modal-cancel" @click="showWithdrawModal = false">취소</button>
              <button class="mp-modal-confirm" :disabled="withdrawing" @click="handleWithdraw">
                {{ withdrawing ? '처리 중...' : '탈퇴하기' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 리포트 -->
        <section class="mp-section">
          <div class="mp-section-hdr">
            <h2 class="mp-section-title">AI 리포트</h2>
            <router-link to="/analysis" class="mp-analysis-link">분석 페이지로 →</router-link>
          </div>

          <!-- 현재 세션 리포트 -->
          <div v-if="reportStore.report" class="mp-report-card">
            <div class="mp-report-head">
              <div>
                <span class="mp-report-kicker">AI REPORT</span>
                <p class="mp-report-title">{{ reportStore.report.draft.title }}</p>
              </div>
              <span class="mp-report-status" :class="{ fallback: reportStore.report.status === 'DRAFT_FALLBACK' }">
                {{ reportStore.report.status === 'COMPLETED' ? 'AI 고도화 완료' : '초안' }}
              </span>
            </div>

            <p class="mp-report-summary">
              {{ reportStore.report.ai_enhancement?.executive_summary?.trim() || reportStore.report.draft.overview }}
            </p>

            <div v-if="reportStore.report.analysis_result?.summary" class="mp-report-metrics">
              <div class="mp-metric">
                <span>분석 지역</span>
                <strong>{{ reportStore.report.analysis_result.summary.region_count ?? '-' }}곳</strong>
              </div>
              <div class="mp-metric">
                <span>상승 / 하락</span>
                <strong>{{ reportStore.report.analysis_result.summary.rising_region_count ?? '-' }} / {{ reportStore.report.analysis_result.summary.falling_region_count ?? '-' }}</strong>
              </div>
              <div class="mp-metric">
                <span>평균 가격 변동</span>
                <strong :class="{ neg: (reportStore.report.analysis_result.summary.avg_price_change_after_window_pct ?? 0) < 0 }">
                  {{ signed(reportStore.report.analysis_result.summary.avg_price_change_after_window_pct) }}
                </strong>
              </div>
              <div class="mp-metric">
                <span>평균 거래량 변동</span>
                <strong :class="{ neg: (reportStore.report.analysis_result.summary.avg_volume_change_after_window_pct ?? 0) < 0 }">
                  {{ signed(reportStore.report.analysis_result.summary.avg_volume_change_after_window_pct) }}
                </strong>
              </div>
            </div>

            <div class="mp-report-meta">생성일: {{ fmtDate(reportStore.report.created_at) }}</div>

            <button class="mp-download-btn" :disabled="reportStore.loading" @click="reportStore.download()">
              {{ reportStore.loading ? 'PDF 준비 중...' : 'PDF 다운로드' }}
            </button>
          </div>

          <!-- 리포트 없음 -->
          <div v-else class="mp-report-empty">
            <div class="mp-empty-icon">📊</div>
            <p>생성된 리포트가 없습니다.</p>
            <p class="mp-empty-sub">분석 페이지에서 이벤트를 선택하고 AI 리포트를 생성해보세요.</p>
            <router-link to="/analysis" class="mp-go-analysis">분석 시작하기 →</router-link>
          </div>
        </section>

      </div>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.mp { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }
.mp-main { flex: 1; padding: 40px 24px; }
.mp-inner { max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 32px; }

.mp-section { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; }
.mp-section-hdr { display: flex; justify-content: space-between; align-items: center; }
.mp-section-title { font-size: 16px; font-weight: 700; color: #1e293b; }
.mp-analysis-link { font-size: 13px; color: #3b82f6; text-decoration: none; }
.mp-analysis-link:hover { text-decoration: underline; }

/* 프로필 카드 */
.mp-loading { padding: 28px 28px; color: #94a3b8; font-size: 14px; }
.mp-profile-card { display: flex; align-items: center; gap: 16px; padding: 28px; }
.mp-avatar { width: 52px; height: 52px; border-radius: 50%; background: #1e293b; color: #fff; font-size: 20px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mp-profile-info { flex: 1; }
.mp-nick { font-size: 18px; font-weight: 700; color: #1e293b; }
.mp-email { font-size: 14px; color: #64748b; margin-top: 2px; }
.mp-logout { padding: 7px 14px; border-radius: 6px; background: none; border: 1px solid #e2e8f0; color: #64748b; font-size: 14px; cursor: pointer; transition: all .15s; font-family: inherit; }
.mp-logout:hover { border-color: #cbd5e1; color: #1e293b; }
.mp-nick-row { display: flex; align-items: center; gap: 8px; }
.mp-nick-edit-btn { padding: 2px 8px; border: 1px solid #e2e8f0; background: none; color: #94a3b8; border-radius: 4px; font-size: 12px; cursor: pointer; transition: all .12s; font-family: inherit; }
.mp-nick-edit-btn:hover { border-color: #cbd5e1; color: #475569; }
.mp-nick-edit { display: flex; flex-direction: column; gap: 6px; }
.mp-nick-input { border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px; font-size: 16px; font-weight: 700; color: #1e293b; font-family: inherit; width: 180px; }
.mp-nick-input:focus { outline: none; border-color: #94a3b8; }
.mp-nick-btns { display: flex; gap: 6px; }
.mp-nick-save { padding: 5px 12px; background: #1e293b; color: #fff; border: none; border-radius: 5px; font-size: 13px; cursor: pointer; font-family: inherit; }
.mp-nick-save:disabled { opacity: .5; cursor: not-allowed; }
.mp-nick-cancel { padding: 5px 12px; background: none; border: 1px solid #e2e8f0; color: #64748b; border-radius: 5px; font-size: 13px; cursor: pointer; font-family: inherit; }
.mp-nick-err { font-size: 12px; color: #ef4444; }
.mp-withdraw-row { padding: 12px 28px 20px; border-top: 1px solid #f1f5f9; }
.mp-withdraw-btn { background: none; border: none; color: #94a3b8; font-size: 12px; cursor: pointer; text-decoration: underline; font-family: inherit; }
.mp-withdraw-btn:hover { color: #ef4444; }
.mp-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 200; display: flex; align-items: center; justify-content: center; }
.mp-modal { background: #fff; border-radius: 16px; padding: 32px; width: 100%; max-width: 400px; box-shadow: 0 20px 60px rgba(0,0,0,.15); }
.mp-modal-title { font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 12px; }
.mp-modal-desc { font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 24px; }
.mp-modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.mp-modal-cancel { padding: 9px 18px; background: none; border: 1px solid #e2e8f0; color: #64748b; border-radius: 8px; font-size: 14px; cursor: pointer; font-family: inherit; }
.mp-modal-confirm { padding: 9px 18px; background: #ef4444; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: inherit; }
.mp-modal-confirm:disabled { opacity: .5; cursor: not-allowed; }

/* 리포트 카드 */
.mp-section-hdr, .mp-report-head ~ * { padding: 0; }
.mp-section > .mp-section-hdr { padding: 24px 28px 0; }
.mp-report-card { padding: 28px; }
.mp-report-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.mp-report-kicker { display: block; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: #3b82f6; margin-bottom: 4px; }
.mp-report-title { font-size: 16px; font-weight: 600; color: #1e293b; line-height: 1.4; }
.mp-report-status { padding: 3px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; background: #dcfce7; color: #16a34a; white-space: nowrap; }
.mp-report-status.fallback { background: #fef9c3; color: #ca8a04; }
.mp-report-summary { font-size: 14px; color: #475569; line-height: 1.7; margin-bottom: 16px; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 4; overflow: hidden; }
.mp-report-metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; padding: 16px; background: #f8fafc; border-radius: 8px; margin-bottom: 16px; }
.mp-metric { display: flex; flex-direction: column; gap: 3px; }
.mp-metric span { font-size: 11px; color: #94a3b8; }
.mp-metric strong { font-size: 15px; font-weight: 700; color: #1e293b; }
.mp-metric strong.neg { color: #ef4444; }
.mp-report-meta { font-size: 12px; color: #94a3b8; margin-bottom: 14px; }
.mp-download-btn { width: 100%; padding: 10px; background: #1e293b; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background .15s; font-family: inherit; }
.mp-download-btn:hover:not(:disabled) { background: #334155; }
.mp-download-btn:disabled { opacity: .5; cursor: not-allowed; }

/* 리포트 없음 */
.mp-report-empty { padding: 60px 28px; text-align: center; }
.mp-empty-icon { font-size: 40px; margin-bottom: 12px; }
.mp-report-empty p { font-size: 15px; color: #475569; font-weight: 500; }
.mp-empty-sub { font-size: 13px; color: #94a3b8; margin-top: 6px; font-weight: 400; }
.mp-go-analysis { display: inline-block; margin-top: 20px; padding: 10px 24px; background: #1e293b; color: #fff; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600; transition: background .15s; }
.mp-go-analysis:hover { background: #334155; }
</style>
