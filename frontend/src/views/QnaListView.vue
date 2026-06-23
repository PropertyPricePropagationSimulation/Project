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

function fmtDate(s: string) { return s?.slice(0, 10) ?? '' }
</script>

<template>
  <div class="pv">
    <AppHeader />
    <main class="pv-main">
      <div class="pv-inner">
        <div class="pv-top">
          <h1 class="pv-title">Q&A</h1>
          <button v-if="authStore.isLoggedIn" class="pv-write-btn"
                  @click="router.push('/qna/write')">질문 작성</button>
          <router-link v-else to="/login" class="pv-write-btn">로그인 후 작성</router-link>
        </div>

        <div v-if="loading" class="pv-loading">불러오는 중...</div>

        <table v-else class="pv-table">
          <thead>
            <tr>
              <th class="pv-th-num">번호</th>
              <th>제목</th>
              <th class="pv-th-s">답변</th>
              <th class="pv-th-w">작성자</th>
              <th class="pv-th-d">날짜</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="qnas.length === 0">
              <td colspan="5" class="pv-empty">등록된 Q&A가 없습니다.</td>
            </tr>
            <tr v-for="q in qnas" :key="q.qnaId" class="pv-row"
                @click="router.push(`/qna/${q.qnaId}`)">
              <td class="pv-num">{{ q.qnaId }}</td>
              <td class="pv-ttl">{{ q.title }}</td>
              <td class="pv-s">
                <span :class="['pv-badge', q.answered ? 'done' : 'wait']">
                  {{ q.answered ? '답변완료' : '대기중' }}
                </span>
              </td>
              <td class="pv-w">{{ q.writer }}</td>
              <td class="pv-d">{{ fmtDate(q.createdAt) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="pv-pg">
          <button :disabled="page <= 1"            @click="goPage(page - 1)" class="pv-pg-btn">‹</button>
          <button v-for="p in totalPages()" :key="p"
                  :class="['pv-pg-btn', { on: p === page }]"
                  @click="goPage(p)">{{ p }}</button>
          <button :disabled="page >= totalPages()" @click="goPage(page + 1)" class="pv-pg-btn">›</button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.pv { min-height: 100vh; background: #f8fafc; }
.pv-main { padding: 40px 24px; }
.pv-inner { max-width: 900px; margin: 0 auto; }
.pv-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.pv-title { font-size: 22px; font-weight: 700; color: #1e293b; }
.pv-write-btn { padding: 8px 18px; background: #1e293b; color: #fff; border: none; border-radius: 7px; font-size: 14px; font-weight: 500; cursor: pointer; text-decoration: none; transition: background .15s; }
.pv-write-btn:hover { background: #334155; }
.pv-loading { text-align: center; color: #94a3b8; padding: 40px; }
.pv-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.pv-table th { padding: 12px 16px; text-align: left; font-size: 13px; font-weight: 600; color: #64748b; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.pv-th-num { width: 60px; }
.pv-th-s   { width: 80px; }
.pv-th-w   { width: 100px; }
.pv-th-d   { width: 110px; }
.pv-row { cursor: pointer; transition: background .12s; }
.pv-row:hover td { background: #f8fafc; }
.pv-table td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: #334155; }
.pv-table tr:last-child td { border-bottom: none; }
.pv-num { color: #94a3b8; font-size: 13px; }
.pv-ttl { font-weight: 500; }
.pv-w, .pv-d { color: #94a3b8; font-size: 13px; }
.pv-empty { text-align: center; color: #94a3b8; padding: 40px; }
.pv-badge { padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.pv-badge.done { background: #dcfce7; color: #16a34a; }
.pv-badge.wait { background: #fef9c3; color: #ca8a04; }
.pv-pg { display: flex; justify-content: center; gap: 4px; margin-top: 24px; }
.pv-pg-btn { min-width: 36px; height: 36px; padding: 0 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px; cursor: pointer; font-size: 14px; color: #475569; transition: all .12s; }
.pv-pg-btn:hover:not(:disabled) { border-color: #cbd5e1; color: #1e293b; }
.pv-pg-btn.on { background: #1e293b; color: #fff; border-color: #1e293b; }
.pv-pg-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
