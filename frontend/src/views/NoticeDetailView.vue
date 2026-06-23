<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { getNotice, type Notice } from '@/api/noticeApi'

const router = useRouter()
const route  = useRoute()
const notice = ref<Notice | null>(null)
const error  = ref(false)

onMounted(async () => {
  try {
    notice.value = await getNotice(Number(route.params.id))
  } catch {
    error.value = true
  }
})

function fmtDate(s: string) { return s?.slice(0, 10) ?? '' }
</script>

<template>
  <div class="pv">
    <AppHeader />
    <main class="pv-main">
      <div class="pv-inner">
        <button class="pv-back" @click="router.push('/notices')">← 목록으로</button>

        <div v-if="error" class="pv-err">공지사항을 불러올 수 없습니다.</div>

        <article v-else-if="notice" class="pv-card">
          <div class="pv-card-hdr">
            <h1 class="pv-card-title">{{ notice.title }}</h1>
            <div class="pv-card-meta">
              <span>{{ notice.writer }}</span>
              <span>{{ fmtDate(notice.createdAt) }}</span>
            </div>
          </div>
          <div class="pv-card-body">{{ notice.content }}</div>
        </article>

        <div v-else class="pv-loading">불러오는 중...</div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.pv { min-height: 100vh; background: #f8fafc; }
.pv-main { padding: 40px 24px; }
.pv-inner { max-width: 800px; margin: 0 auto; }
.pv-back { background: none; border: 1px solid #e2e8f0; color: #64748b; padding: 7px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; margin-bottom: 24px; transition: all .12s; }
.pv-back:hover { color: #1e293b; border-color: #cbd5e1; }
.pv-loading, .pv-err { text-align: center; color: #94a3b8; padding: 60px; }
.pv-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; }
.pv-card-hdr { padding: 28px 32px 20px; border-bottom: 1px solid #f1f5f9; }
.pv-card-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
.pv-card-meta { display: flex; gap: 12px; font-size: 13px; color: #94a3b8; }
.pv-card-body { padding: 28px 32px; font-size: 15px; color: #334155; line-height: 1.8; white-space: pre-wrap; }
</style>
