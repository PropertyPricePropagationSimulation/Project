<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { useAuthStore } from '@/stores/authStore'
import { getQnas, type Qna } from '@/api/qnaApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const qnas       = ref<Qna[]>([])
const totalCount = ref(0)
const page       = ref(Number(route.query.page) || 1)
const PAGE_SIZE  = 10
const loading    = ref(false)

const myId = () => {
  try {
    const token = authStore.accessToken ?? ''
    if (!token) return null
    return Number(JSON.parse(atob(token.split('.')[1] ?? '')).sub)
  } catch { return null }
}

async function load() {
  loading.value = true
  try {
    const res = await getQnas(page.value, PAGE_SIZE)
    qnas.value       = res.content
    totalCount.value = res.totalCount
  } finally {
    loading.value = false
  }
}

const totalPages = () => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE))

function goPage(p: number) {
  page.value = p
  router.push({ query: { page: p } })
}

onMounted(load)
watch(page, load)

function fmtDate(s: string) {
  if (!s) return ''
  const d = new Date(s)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '방금 전'
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}일 전`
  return s.slice(0, 10)
}
</script>

<template>
  <div class="qv">
    <AppHeader />
    <main class="qv-main">
      <div class="qv-inner">

        <div class="qv-top">
          <div class="qv-top-left">
            <h1 class="qv-title">Q&A</h1>
            <span class="qv-count">총 {{ totalCount }}건</span>
          </div>
          <button v-if="authStore.isLoggedIn" class="qv-write-btn" @click="router.push('/qna/write')">
            질문 작성
          </button>
          <router-link v-else to="/login" class="qv-write-btn">로그인 후 작성</router-link>
        </div>

        <div v-if="loading" class="qv-loading">
          <div class="qv-skeleton" v-for="i in 5" :key="i" />
        </div>

        <ul v-else class="qv-list">
          <li v-if="qnas.length === 0" class="qv-empty">
            <div class="qv-empty-icon">💬</div>
            <p>등록된 Q&A가 없습니다.</p>
            <p class="qv-empty-sub">첫 번째 질문을 남겨보세요.</p>
          </li>
          <li
            v-for="(q, idx) in qnas"
            :key="q.qnaId"
            class="qv-item"
            :class="{ mine: myId() === q.writerId }"
            @click="router.push(`/qna/${q.qnaId}`)"
          >
            <div class="qv-item-left">
              <span class="qv-num">{{ totalCount - (page - 1) * PAGE_SIZE - idx }}</span>
              <div class="qv-item-body">
                <div class="qv-item-title-row">
                  <p class="qv-item-title">{{ q.title }}</p>
                  <span v-if="myId() === q.writerId" class="qv-mine-badge">내 글</span>
                </div>
                <div class="qv-item-meta">
                  <span class="qv-writer">{{ q.writer }}</span>
                  <span class="qv-dot">·</span>
                  <span class="qv-date">{{ fmtDate(q.createdAt) }}</span>
                </div>
              </div>
            </div>
            <span :class="['qv-badge', q.answered ? 'done' : 'wait']">
              {{ q.answered ? '답변완료' : '대기중' }}
            </span>
          </li>
        </ul>

        <div class="qv-pg">
          <button :disabled="page <= 1" @click="goPage(page - 1)" class="qv-pg-btn">‹</button>
          <button
            v-for="p in totalPages()" :key="p"
            :class="['qv-pg-btn', { on: p === page }]"
            @click="goPage(p)"
          >{{ p }}</button>
          <button :disabled="page >= totalPages()" @click="goPage(page + 1)" class="qv-pg-btn">›</button>
        </div>

      </div>
    </main>
  </div>
</template>

<style scoped>
.qv { min-height: 100vh; background: #f8fafc; }
.qv-main { padding: 40px 24px; }
.qv-inner { max-width: 900px; margin: 0 auto; }

.qv-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.qv-top-left { display: flex; align-items: baseline; gap: 12px; }
.qv-title { font-size: 22px; font-weight: 700; color: #1e293b; }
.qv-count { font-size: 13px; color: #94a3b8; }
.qv-write-btn { padding: 9px 18px; background: #1e293b; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; text-decoration: none; transition: background .15s; font-family: inherit; }
.qv-write-btn:hover { background: #334155; }

/* 로딩 스켈레톤 */
.qv-loading { display: flex; flex-direction: column; gap: 1px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.qv-skeleton { height: 72px; background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* 목록 */
.qv-list { list-style: none; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.qv-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 18px 20px; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background .12s; }
.qv-item:last-child { border-bottom: none; }
.qv-item:hover { background: #f8fafc; }
.qv-item.mine { background: #fafbff; }
.qv-item-left { display: flex; align-items: center; gap: 16px; flex: 1; min-width: 0; }
.qv-num { font-size: 12px; color: #cbd5e1; font-weight: 600; min-width: 28px; text-align: center; flex-shrink: 0; }
.qv-item-body { flex: 1; min-width: 0; }
.qv-item-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.qv-item-title { font-size: 15px; font-weight: 500; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.qv-item:hover .qv-item-title { color: #3b82f6; }
.qv-mine-badge { font-size: 10px; font-weight: 600; padding: 1px 6px; background: #eff6ff; color: #3b82f6; border-radius: 10px; flex-shrink: 0; }
.qv-item-meta { display: flex; align-items: center; gap: 6px; }
.qv-writer { font-size: 12px; color: #94a3b8; }
.qv-dot { font-size: 12px; color: #cbd5e1; }
.qv-date { font-size: 12px; color: #94a3b8; }
.qv-badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.qv-badge.done { background: #dcfce7; color: #16a34a; }
.qv-badge.wait { background: #fef9c3; color: #ca8a04; }

/* 비어있음 */
.qv-empty { padding: 60px 20px; text-align: center; }
.qv-empty-icon { font-size: 36px; margin-bottom: 12px; }
.qv-empty p { font-size: 14px; color: #94a3b8; font-weight: 500; }
.qv-empty-sub { font-size: 13px; color: #cbd5e1; margin-top: 4px; font-weight: 400; }

/* 페이지네이션 */
.qv-pg { display: flex; justify-content: center; gap: 4px; margin-top: 24px; }
.qv-pg-btn { min-width: 36px; height: 36px; padding: 0 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px; cursor: pointer; font-size: 14px; color: #475569; transition: all .12s; }
.qv-pg-btn:hover:not(:disabled) { border-color: #cbd5e1; color: #1e293b; }
.qv-pg-btn.on { background: #1e293b; color: #fff; border-color: #1e293b; }
.qv-pg-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
