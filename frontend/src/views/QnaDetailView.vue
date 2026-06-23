<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { useAuthStore } from '@/stores/authStore'
import { getQna, getComments, createComment, deleteComment, deleteQna, type Qna, type QnaComment } from '@/api/qnaApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const qnaId    = Number(route.params.id)
const qna      = ref<Qna | null>(null)
const comments = ref<QnaComment[]>([])
const newComment = ref('')
const submitting = ref(false)
const error      = ref(false)

async function load() {
  try {
    ;[qna.value, comments.value] = await Promise.all([getQna(qnaId), getComments(qnaId)])
  } catch {
    error.value = true
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    await createComment(qnaId, newComment.value.trim())
    newComment.value = ''
    comments.value = await getComments(qnaId)
  } finally {
    submitting.value = false
  }
}

async function handleDeleteComment(commentId: number) {
  if (!confirm('댓글을 삭제할까요?')) return
  await deleteComment(qnaId, commentId)
  comments.value = await getComments(qnaId)
}

async function handleDeleteQna() {
  if (!confirm('Q&A를 삭제할까요?')) return
  await deleteQna(qnaId)
  router.push('/qna')
}

onMounted(load)

function fmtDate(s: string) { return s?.slice(0, 10) ?? '' }

const myId = () => {
  const token = authStore.accessToken
  if (!token) return null
  try { return Number(JSON.parse(atob(token.split('.')[1])).sub) } catch { return null }
}
</script>

<template>
  <div class="pv">
    <AppHeader />
    <main class="pv-main">
      <div class="pv-inner">
        <button class="pv-back" @click="router.push('/qna')">← 목록으로</button>

        <div v-if="error" class="pv-err">Q&A를 불러올 수 없습니다.</div>

        <template v-else-if="qna">
          <article class="pv-card">
            <div class="pv-card-hdr">
              <div class="pv-card-top">
                <h1 class="pv-card-title">{{ qna.title }}</h1>
                <span :class="['pv-badge', qna.answered ? 'done' : 'wait']">
                  {{ qna.answered ? '답변완료' : '대기중' }}
                </span>
              </div>
              <div class="pv-card-meta">
                <span>{{ qna.writer }}</span>
                <span>{{ fmtDate(qna.createdAt) }}</span>
                <button v-if="myId() === qna.writerId" class="pv-del-btn"
                        @click="handleDeleteQna">삭제</button>
              </div>
            </div>
            <div class="pv-card-body">{{ qna.content }}</div>
          </article>

          <!-- COMMENTS -->
          <section class="pv-comments">
            <h2 class="pv-cmt-hdr">댓글 {{ comments.length }}</h2>

            <ul class="pv-cmt-list">
              <li v-if="comments.length === 0" class="pv-cmt-empty">첫 번째 댓글을 남겨보세요.</li>
              <li v-for="c in comments" :key="c.commentId" class="pv-cmt-item">
                <div class="pv-cmt-top">
                  <span class="pv-cmt-writer">{{ c.writer }}</span>
                  <span class="pv-cmt-date">{{ fmtDate(c.createdAt) }}</span>
                  <button v-if="myId() === c.writerId" class="pv-cmt-del"
                          @click="handleDeleteComment(c.commentId)">삭제</button>
                </div>
                <p class="pv-cmt-body">{{ c.content }}</p>
              </li>
            </ul>

            <div v-if="authStore.isLoggedIn" class="pv-cmt-form">
              <textarea v-model="newComment" placeholder="댓글을 입력하세요" class="pv-cmt-ta" rows="3" />
              <button class="pv-cmt-submit" :disabled="submitting || !newComment.trim()"
                      @click="submitComment">
                {{ submitting ? '등록 중...' : '댓글 등록' }}
              </button>
            </div>
            <p v-else class="pv-cmt-login">
              <router-link to="/login">로그인</router-link> 후 댓글을 작성할 수 있습니다.
            </p>
          </section>
        </template>

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
.pv-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; margin-bottom: 24px; }
.pv-card-hdr { padding: 28px 32px 20px; border-bottom: 1px solid #f1f5f9; }
.pv-card-top { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pv-card-title { font-size: 20px; font-weight: 700; color: #1e293b; flex: 1; }
.pv-badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.pv-badge.done { background: #dcfce7; color: #16a34a; }
.pv-badge.wait { background: #fef9c3; color: #ca8a04; }
.pv-card-meta { display: flex; align-items: center; gap: 12px; font-size: 13px; color: #94a3b8; }
.pv-del-btn { padding: 3px 10px; border: 1px solid #fca5a5; background: none; color: #ef4444; border-radius: 4px; font-size: 12px; cursor: pointer; margin-left: auto; }
.pv-card-body { padding: 28px 32px; font-size: 15px; color: #334155; line-height: 1.8; white-space: pre-wrap; }
.pv-comments { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); padding: 24px 32px; }
.pv-cmt-hdr { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 16px; }
.pv-cmt-list { list-style: none; }
.pv-cmt-empty { color: #94a3b8; font-size: 14px; padding: 20px 0; }
.pv-cmt-item { padding: 16px 0; border-bottom: 1px solid #f1f5f9; }
.pv-cmt-item:last-child { border-bottom: none; }
.pv-cmt-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.pv-cmt-writer { font-size: 13px; font-weight: 600; color: #334155; }
.pv-cmt-date { font-size: 12px; color: #94a3b8; }
.pv-cmt-del { margin-left: auto; padding: 2px 8px; border: 1px solid #fca5a5; background: none; color: #ef4444; border-radius: 4px; font-size: 11px; cursor: pointer; }
.pv-cmt-body { font-size: 14px; color: #475569; line-height: 1.6; }
.pv-cmt-form { margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; }
.pv-cmt-ta { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 14px; color: #334155; resize: vertical; font-family: inherit; }
.pv-cmt-ta:focus { outline: none; border-color: #94a3b8; }
.pv-cmt-submit { margin-top: 10px; padding: 9px 20px; background: #1e293b; color: #fff; border: none; border-radius: 7px; font-size: 14px; cursor: pointer; }
.pv-cmt-submit:disabled { opacity: .5; cursor: not-allowed; }
.pv-cmt-login { margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; font-size: 14px; color: #94a3b8; }
.pv-cmt-login a { color: #3b82f6; text-decoration: none; }
</style>
