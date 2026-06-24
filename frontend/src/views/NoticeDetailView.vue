<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useAuthStore } from '@/stores/authStore'
import { getNotice, updateNotice, deleteNotice, type Notice } from '@/api/noticeApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const noticeId = Number(route.params.id)
const notice   = ref<Notice | null>(null)
const error    = ref(false)
const editing  = ref(false)
const editTitle   = ref('')
const editContent = ref('')
const saving   = ref(false)

onMounted(async () => {
  try {
    notice.value = await getNotice(noticeId)
  } catch {
    error.value = true
  }
})

function startEdit() {
  if (!notice.value) return
  editTitle.value   = notice.value.title
  editContent.value = notice.value.content
  editing.value     = true
}

async function saveEdit() {
  if (!editTitle.value.trim() || !editContent.value.trim()) return
  saving.value = true
  try {
    await updateNotice(noticeId, editTitle.value.trim(), editContent.value.trim())
    notice.value  = await getNotice(noticeId)
    editing.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!confirm('공지사항을 삭제할까요?')) return
  await deleteNotice(noticeId)
  router.push('/notices')
}

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
          <!-- 수정 모드 -->
          <div v-if="editing" class="pv-edit-form">
            <input v-model="editTitle" class="pv-edit-title" placeholder="제목" />
            <textarea v-model="editContent" class="pv-edit-content" rows="10" placeholder="내용" />
            <div class="pv-edit-actions">
              <button class="pv-save-btn" :disabled="saving" @click="saveEdit">
                {{ saving ? '저장 중...' : '저장' }}
              </button>
              <button class="pv-cancel-btn" @click="editing = false">취소</button>
            </div>
          </div>

          <!-- 보기 모드 -->
          <template v-else>
            <div class="pv-card-hdr">
              <h1 class="pv-card-title">{{ notice.title }}</h1>
              <div class="pv-card-meta">
                <span>{{ notice.writer }}</span>
                <span>{{ fmtDate(notice.createdAt) }}</span>
                <div v-if="authStore.isAdmin" class="pv-actions">
                  <button class="pv-edit-btn" @click="startEdit">수정</button>
                  <button class="pv-del-btn" @click="handleDelete">삭제</button>
                </div>
              </div>
            </div>
            <div class="pv-card-body">{{ notice.content }}</div>
          </template>
        </article>

        <div v-else class="pv-loading">불러오는 중...</div>
      </div>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.pv { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; }
.pv-main { flex: 1; padding: 40px 24px; }
.pv-inner { max-width: 800px; margin: 0 auto; }
.pv-back { background: none; border: 1px solid #e2e8f0; color: #64748b; padding: 7px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; margin-bottom: 24px; transition: all .12s; }
.pv-back:hover { color: #1e293b; border-color: #cbd5e1; }
.pv-loading, .pv-err { text-align: center; color: #94a3b8; padding: 60px; }
.pv-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; }
.pv-card-hdr { padding: 28px 32px 20px; border-bottom: 1px solid #f1f5f9; }
.pv-card-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
.pv-card-meta { display: flex; align-items: center; gap: 12px; font-size: 13px; color: #94a3b8; }
.pv-card-body { padding: 28px 32px; font-size: 15px; color: #334155; line-height: 1.8; white-space: pre-wrap; }
.pv-actions { display: flex; gap: 6px; margin-left: auto; }
.pv-edit-btn { padding: 3px 10px; border: 1px solid #cbd5e1; background: none; color: #475569; border-radius: 4px; font-size: 12px; cursor: pointer; }
.pv-edit-btn:hover { border-color: #94a3b8; color: #1e293b; }
.pv-del-btn { padding: 3px 10px; border: 1px solid #fca5a5; background: none; color: #ef4444; border-radius: 4px; font-size: 12px; cursor: pointer; }
.pv-edit-form { padding: 28px 32px; display: flex; flex-direction: column; gap: 12px; }
.pv-edit-title { border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; font-size: 16px; font-weight: 600; color: #1e293b; font-family: inherit; }
.pv-edit-title:focus { outline: none; border-color: #94a3b8; }
.pv-edit-content { border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; font-size: 14px; color: #334155; resize: vertical; font-family: inherit; line-height: 1.7; }
.pv-edit-content:focus { outline: none; border-color: #94a3b8; }
.pv-edit-actions { display: flex; gap: 8px; }
.pv-save-btn { padding: 9px 20px; background: #1e293b; color: #fff; border: none; border-radius: 7px; font-size: 14px; cursor: pointer; font-family: inherit; }
.pv-save-btn:disabled { opacity: .5; cursor: not-allowed; }
.pv-cancel-btn { padding: 9px 20px; background: none; border: 1px solid #e2e8f0; color: #64748b; border-radius: 7px; font-size: 14px; cursor: pointer; font-family: inherit; }
</style>
