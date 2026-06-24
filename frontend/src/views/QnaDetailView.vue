<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { useAuthStore } from '@/stores/authStore'
import { getQna, getComments, createComment, updateComment, deleteComment, deleteQna, updateQna, updateAnswered, type Qna, type QnaComment } from '@/api/qnaApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const qnaId      = Number(route.params.id)
const qna        = ref<Qna | null>(null)
const comments   = ref<QnaComment[]>([])
const newComment = ref('')
const submitting = ref(false)
const error      = ref(false)
const editing    = ref(false)
const editTitle   = ref('')
const editContent = ref('')
const saving     = ref(false)
const editingCommentId      = ref<number | null>(null)
const editingCommentContent = ref('')
const savingComment         = ref(false)

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

function startEditComment(c: QnaComment) {
  editingCommentId.value      = c.commentId
  editingCommentContent.value = c.content
}

async function saveEditComment(commentId: number) {
  if (!editingCommentContent.value.trim()) return
  savingComment.value = true
  try {
    await updateComment(qnaId, commentId, editingCommentContent.value.trim())
    comments.value = await getComments(qnaId)
    editingCommentId.value = null
  } finally {
    savingComment.value = false
  }
}

async function handleDeleteComment(commentId: number) {
  if (!confirm('댓글을 삭제할까요?')) return
  await deleteComment(qnaId, commentId)
  comments.value = await getComments(qnaId)
}

function startEdit() {
  if (!qna.value) return
  editTitle.value   = qna.value.title
  editContent.value = qna.value.content
  editing.value     = true
}

async function saveEdit() {
  if (!editTitle.value.trim() || !editContent.value.trim()) return
  saving.value = true
  try {
    await updateQna(qnaId, editTitle.value.trim(), editContent.value.trim())
    await load()
    editing.value = false
  } finally {
    saving.value = false
  }
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
  try { return Number(JSON.parse(atob(token.split('.')[1] ?? '')).sub) } catch { return null }
}

async function toggleAnswered() {
  if (!qna.value) return
  await updateAnswered(qnaId, !qna.value.answered)
  await load()
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
            <!-- 수정 모드 -->
            <div v-if="editing" class="pv-edit-form">
              <input v-model="editTitle" class="pv-edit-title" placeholder="제목" />
              <textarea v-model="editContent" class="pv-edit-content" rows="8" placeholder="내용" />
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
                <div class="pv-card-top">
                  <h1 class="pv-card-title">{{ qna.title }}</h1>
                  <span :class="['pv-badge', qna.answered ? 'done' : 'wait']">
                    {{ qna.answered ? '답변완료' : '대기중' }}
                  </span>
                </div>
                <div class="pv-card-meta">
                  <span>{{ qna.writer }}</span>
                  <span>{{ fmtDate(qna.createdAt) }}</span>
                  <div v-if="myId() === qna.writerId || authStore.isAdmin" class="pv-actions">
                    <button
                      :class="['pv-answered-btn', qna.answered ? 'answered' : 'unanswered']"
                      @click="toggleAnswered"
                    >
                      {{ qna.answered ? '답변 취소' : '답변 완료' }}
                    </button>
                    <template v-if="myId() === qna.writerId">
                      <button class="pv-edit-btn" @click="startEdit">수정</button>
                      <button class="pv-del-btn" @click="handleDeleteQna">삭제</button>
                    </template>
                  </div>
                </div>
              </div>
              <div class="pv-card-body">{{ qna.content }}</div>
            </template>
          </article>

          <!-- COMMENTS -->
          <section class="pv-comments">
            <h2 class="pv-cmt-hdr">댓글 {{ comments.length }}</h2>

            <ul class="pv-cmt-list">
              <li v-if="comments.length === 0" class="pv-cmt-empty">첫 번째 댓글을 남겨보세요.</li>
              <li v-for="c in comments" :key="c.commentId" class="pv-cmt-item">
                <!-- 수정 모드 -->
                <template v-if="editingCommentId === c.commentId">
                  <div class="pv-cmt-top">
                    <span class="pv-cmt-writer">{{ c.writer }}</span>
                    <span class="pv-cmt-date">{{ fmtDate(c.createdAt) }}</span>
                  </div>
                  <textarea v-model="editingCommentContent" class="pv-cmt-ta pv-cmt-edit-ta" rows="3" />
                  <div class="pv-cmt-edit-actions">
                    <button class="pv-cmt-save" :disabled="savingComment" @click="saveEditComment(c.commentId)">
                      {{ savingComment ? '저장 중...' : '저장' }}
                    </button>
                    <button class="pv-cmt-cancel" @click="editingCommentId = null">취소</button>
                  </div>
                </template>
                <!-- 보기 모드 -->
                <template v-else>
                  <div class="pv-cmt-top">
                    <span class="pv-cmt-writer">{{ c.writer }}</span>
                    <span class="pv-cmt-date">{{ fmtDate(c.createdAt) }}</span>
                    <template v-if="myId() === c.writerId">
                      <button class="pv-cmt-edit-btn" @click="startEditComment(c)">수정</button>
                      <button class="pv-cmt-del" @click="handleDeleteComment(c.commentId)">삭제</button>
                    </template>
                  </div>
                  <p class="pv-cmt-body">{{ c.content }}</p>
                </template>
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
.pv-card { background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); overflow: hidden; margin-bottom: 24px; }
.pv-card-hdr { padding: 28px 32px 20px; border-bottom: 1px solid #f1f5f9; }
.pv-card-top { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pv-card-title { font-size: 20px; font-weight: 700; color: #1e293b; flex: 1; }
.pv-badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.pv-badge.done { background: #dcfce7; color: #16a34a; }
.pv-badge.wait { background: #fef9c3; color: #ca8a04; }
.pv-card-meta { display: flex; align-items: center; gap: 12px; font-size: 13px; color: #94a3b8; }
.pv-actions { display: flex; gap: 6px; margin-left: auto; }
.pv-answered-btn { padding: 3px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; border: 1px solid; }
.pv-answered-btn.unanswered { border-color: #6ee7b7; background: none; color: #059669; }
.pv-answered-btn.unanswered:hover { background: #ecfdf5; }
.pv-answered-btn.answered { border-color: #fcd34d; background: none; color: #d97706; }
.pv-answered-btn.answered:hover { background: #fffbeb; }
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
.pv-cmt-edit-btn { margin-left: auto; padding: 2px 8px; border: 1px solid #cbd5e1; background: none; color: #475569; border-radius: 4px; font-size: 11px; cursor: pointer; }
.pv-cmt-edit-btn:hover { border-color: #94a3b8; color: #1e293b; }
.pv-cmt-del { padding: 2px 8px; border: 1px solid #fca5a5; background: none; color: #ef4444; border-radius: 4px; font-size: 11px; cursor: pointer; }
.pv-cmt-edit-ta { margin-top: 6px; }
.pv-cmt-edit-actions { display: flex; gap: 6px; margin-top: 8px; }
.pv-cmt-save { padding: 6px 16px; background: #1e293b; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; font-family: inherit; }
.pv-cmt-save:disabled { opacity: .5; cursor: not-allowed; }
.pv-cmt-cancel { padding: 6px 16px; background: none; border: 1px solid #e2e8f0; color: #64748b; border-radius: 6px; font-size: 13px; cursor: pointer; font-family: inherit; }
.pv-cmt-body { font-size: 14px; color: #475569; line-height: 1.6; }
.pv-cmt-form { margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; }
.pv-cmt-ta { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 14px; color: #334155; resize: vertical; font-family: inherit; }
.pv-cmt-ta:focus { outline: none; border-color: #94a3b8; }
.pv-cmt-submit { margin-top: 10px; padding: 9px 20px; background: #1e293b; color: #fff; border: none; border-radius: 7px; font-size: 14px; cursor: pointer; }
.pv-cmt-submit:disabled { opacity: .5; cursor: not-allowed; }
.pv-cmt-login { margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; font-size: 14px; color: #94a3b8; }
.pv-cmt-login a { color: #3b82f6; text-decoration: none; }
</style>
