<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { createQna } from '@/api/qnaApi'
import { parseApiError } from '@/api/errorUtils'

const router  = useRouter()
const title   = ref('')
const content = ref('')
const submitting = ref(false)
const error      = ref('')

async function submit() {
  if (!title.value.trim() || !content.value.trim()) {
    error.value = '제목과 내용을 모두 입력해주세요.'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await createQna(title.value.trim(), content.value.trim())
    router.push('/qna')
  } catch (e) {
    error.value = parseApiError(e, '등록 중 오류가 발생했습니다. 다시 시도해주세요.')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="pv">
    <AppHeader />
    <main class="pv-main">
      <div class="pv-inner">
        <button class="pv-back" @click="router.push('/qna')">← Q&A 목록</button>
        <h1 class="pv-title">질문 작성</h1>

        <div class="pv-form">
          <label class="pv-label">제목</label>
          <input v-model="title" type="text" class="pv-input" placeholder="제목을 입력하세요" maxlength="200" />

          <label class="pv-label">내용</label>
          <textarea v-model="content" class="pv-ta" placeholder="질문 내용을 상세히 작성해주세요" rows="12" />

          <p v-if="error" class="pv-error">{{ error }}</p>

          <div class="pv-actions">
            <button class="pv-cancel" @click="router.push('/qna')">취소</button>
            <button class="pv-submit" :disabled="submitting" @click="submit">
              {{ submitting ? '등록 중...' : '질문 등록' }}
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.pv { min-height: 100vh; background: #f8fafc; }
.pv-main { padding: 40px 24px; }
.pv-inner { max-width: 720px; margin: 0 auto; }
.pv-back { background: none; border: 1px solid #e2e8f0; color: #64748b; padding: 7px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; margin-bottom: 20px; transition: all .12s; }
.pv-back:hover { color: #1e293b; border-color: #cbd5e1; }
.pv-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 28px; }
.pv-form { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); padding: 32px; }
.pv-label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px; margin-top: 20px; }
.pv-label:first-child { margin-top: 0; }
.pv-input { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 11px 14px; font-size: 14px; color: #1e293b; font-family: inherit; transition: border-color .12s; }
.pv-input:focus { outline: none; border-color: #94a3b8; }
.pv-ta { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 11px 14px; font-size: 14px; color: #1e293b; resize: vertical; font-family: inherit; transition: border-color .12s; }
.pv-ta:focus { outline: none; border-color: #94a3b8; }
.pv-error { color: #ef4444; font-size: 13px; margin-top: 12px; }
.pv-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
.pv-cancel { padding: 10px 20px; border: 1px solid #e2e8f0; background: none; color: #64748b; border-radius: 8px; font-size: 14px; cursor: pointer; }
.pv-submit { padding: 10px 24px; background: #1e293b; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background .15s; }
.pv-submit:hover:not(:disabled) { background: #334155; }
.pv-submit:disabled { opacity: .5; cursor: not-allowed; }
</style>
