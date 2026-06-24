<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useAuthStore } from '@/stores/authStore'
import { getNotices, deleteNotice, type Notice } from '@/api/noticeApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const notices    = ref<Notice[]>([])
const totalCount = ref(0)
const page       = ref(Number(route.query.page) || 1)
const PAGE_SIZE  = 10
const loading    = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getNotices(page.value, PAGE_SIZE)
    notices.value    = res.content
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

async function handleDelete(e: Event, id: number) {
  e.stopPropagation()
  if (!confirm('공지사항을 삭제할까요?')) return
  await deleteNotice(id)
  await load()
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
  <div class="nv">
    <AppHeader />
    <main class="nv-main">
      <div class="nv-inner">

        <div class="nv-top">
          <h1 class="nv-title">공지사항</h1>
          <span class="nv-count">총 {{ totalCount }}건</span>
          <button v-if="authStore.isAdmin" class="nv-write-btn" @click="router.push('/notices/write')">
            + 공지 작성
          </button>
        </div>

        <div v-if="loading" class="nv-loading">
          <div class="nv-skeleton" v-for="i in 5" :key="i" />
        </div>

        <ul v-else class="nv-list">
          <li v-if="notices.length === 0" class="nv-empty">
            <div class="nv-empty-icon">📋</div>
            <p>등록된 공지사항이 없습니다.</p>
          </li>
          <li
            v-for="(n, idx) in notices"
            :key="n.noticeId"
            class="nv-item"
            @click="router.push(`/notices/${n.noticeId}`)"
          >
            <div class="nv-item-left">
              <span class="nv-num">{{ totalCount - (page - 1) * PAGE_SIZE - idx }}</span>
              <div class="nv-item-body">
                <p class="nv-item-title">{{ n.title }}</p>
                <div class="nv-item-meta">
                  <span class="nv-writer">{{ n.writer }}</span>
                  <span class="nv-dot">·</span>
                  <span class="nv-date">{{ fmtDate(n.createdAt) }}</span>
                </div>
              </div>
            </div>
            <div class="nv-item-right">
              <svg class="nv-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
              <button v-if="authStore.isAdmin" class="nv-del-btn" @click="handleDelete($event, n.noticeId)">삭제</button>
            </div>
          </li>
        </ul>

        <div class="nv-pg">
          <button :disabled="page <= 1" @click="goPage(page - 1)" class="nv-pg-btn">‹</button>
          <button
            v-for="p in totalPages()" :key="p"
            :class="['nv-pg-btn', { on: p === page }]"
            @click="goPage(p)"
          >{{ p }}</button>
          <button :disabled="page >= totalPages()" @click="goPage(page + 1)" class="nv-pg-btn">›</button>
        </div>

      </div>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.nv { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }
.nv-main { flex: 1; padding: 40px 24px; }
.nv-inner { max-width: 900px; margin: 0 auto; }

.nv-top { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.nv-title { font-size: 22px; font-weight: 700; color: #1e293b; }
.nv-count { font-size: 13px; color: #94a3b8; }
.nv-write-btn { margin-left: auto; padding: 8px 16px; background: #1e293b; color: #fff; border: none; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; transition: background .12s; }
.nv-write-btn:hover { background: #334155; }

/* 로딩 스켈레톤 */
.nv-loading { display: flex; flex-direction: column; gap: 1px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.nv-skeleton { height: 72px; background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* 목록 */
.nv-list { list-style: none; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.nv-item { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background .12s; }
.nv-item:last-child { border-bottom: none; }
.nv-item:hover { background: #f8fafc; }
.nv-item-left { display: flex; align-items: center; gap: 16px; flex: 1; min-width: 0; }
.nv-num { font-size: 12px; color: #cbd5e1; font-weight: 600; min-width: 28px; text-align: center; flex-shrink: 0; }
.nv-item-body { flex: 1; min-width: 0; }
.nv-item-title { font-size: 15px; font-weight: 500; color: #1e293b; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nv-item:hover .nv-item-title { color: #3b82f6; }
.nv-item-meta { display: flex; align-items: center; gap: 6px; }
.nv-writer { font-size: 12px; color: #94a3b8; }
.nv-dot { font-size: 12px; color: #cbd5e1; }
.nv-date { font-size: 12px; color: #94a3b8; }
.nv-item-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.nv-arrow { width: 16px; height: 16px; color: #cbd5e1; transition: color .12s; }
.nv-item:hover .nv-arrow { color: #94a3b8; }
.nv-del-btn { padding: 3px 10px; border: 1px solid #fca5a5; background: none; color: #ef4444; border-radius: 4px; font-size: 11px; cursor: pointer; }

/* 비어있음 */
.nv-empty { padding: 60px 20px; text-align: center; }
.nv-empty-icon { font-size: 36px; margin-bottom: 12px; }
.nv-empty p { font-size: 14px; color: #94a3b8; }

/* 페이지네이션 */
.nv-pg { display: flex; justify-content: center; gap: 4px; margin-top: 24px; }
.nv-pg-btn { min-width: 36px; height: 36px; padding: 0 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px; cursor: pointer; font-size: 14px; color: #475569; transition: all .12s; }
.nv-pg-btn:hover:not(:disabled) { border-color: #cbd5e1; color: #1e293b; }
.nv-pg-btn.on { background: #1e293b; color: #fff; border-color: #1e293b; }
.nv-pg-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
