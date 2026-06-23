<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { getNotices, type Notice } from '@/api/noticeApi'

const router  = useRouter()
const route   = useRoute()

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

onMounted(load)
watch(page, load)

function fmtDate(s: string) { return s?.slice(0, 10) ?? '' }
</script>

<template>
  <div class="pv">
    <AppHeader />
    <main class="pv-main">
      <div class="pv-inner">
        <h1 class="pv-title">공지사항</h1>

        <div v-if="loading" class="pv-loading">불러오는 중...</div>

        <table v-else class="pv-table">
          <thead>
            <tr>
              <th class="pv-th-num">번호</th>
              <th>제목</th>
              <th class="pv-th-w">작성자</th>
              <th class="pv-th-d">날짜</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="notices.length === 0">
              <td colspan="4" class="pv-empty">등록된 공지사항이 없습니다.</td>
            </tr>
            <tr v-for="n in notices" :key="n.noticeId" class="pv-row"
                @click="router.push(`/notices/${n.noticeId}`)">
              <td class="pv-num">{{ n.noticeId }}</td>
              <td class="pv-ttl">{{ n.title }}</td>
              <td class="pv-w">{{ n.writer }}</td>
              <td class="pv-d">{{ fmtDate(n.createdAt) }}</td>
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
.pv-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 24px; }
.pv-loading { text-align: center; color: #94a3b8; padding: 40px; }
.pv-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.pv-table th { padding: 12px 16px; text-align: left; font-size: 13px; font-weight: 600; color: #64748b; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.pv-th-num { width: 60px; }
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
.pv-pg { display: flex; justify-content: center; gap: 4px; margin-top: 24px; }
.pv-pg-btn { min-width: 36px; height: 36px; padding: 0 8px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px; cursor: pointer; font-size: 14px; color: #475569; transition: all .12s; }
.pv-pg-btn:hover:not(:disabled) { border-color: #cbd5e1; color: #1e293b; }
.pv-pg-btn.on { background: #1e293b; color: #fff; border-color: #1e293b; }
.pv-pg-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
