<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { parseApiError } from '@/api/errorUtils'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const form = reactive({ email: '', password: '' })
const fieldErrors = reactive({ email: '', password: '' })
const apiError = ref('')
const loading  = ref(false)

function validate(): boolean {
  fieldErrors.email    = ''
  fieldErrors.password = ''
  apiError.value = ''
  let ok = true

  if (!form.email) {
    fieldErrors.email = '이메일을 입력해주세요.'
    ok = false
  }
  if (!form.password) {
    fieldErrors.password = '비밀번호를 입력해주세요.'
    ok = false
  }
  return ok
}

async function submit() {
  if (!validate()) return
  loading.value = true
  try {
    await authStore.login(form.email, form.password)
    const redirect = route.query.redirect as string | undefined
    router.push(redirect ?? '/')
  } catch (e) {
    apiError.value = parseApiError(e, '이메일 또는 비밀번호가 올바르지 않습니다.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="lv">
    <div class="lv-card">
      <router-link to="/" class="lv-logo">
        <span class="lv-logo-sq">EF</span>
        <span class="lv-logo-nm">EstateFlow</span>
      </router-link>

      <h1 class="lv-title">로그인</h1>

      <div class="lv-form">
        <div class="lv-field">
          <label class="lv-label">이메일</label>
          <input v-model="form.email" type="email" :class="['lv-input', { err: fieldErrors.email }]"
                 placeholder="이메일 주소" @keyup.enter="submit" />
          <span v-if="fieldErrors.email" class="lv-ferr">{{ fieldErrors.email }}</span>
        </div>

        <div class="lv-field">
          <label class="lv-label">비밀번호</label>
          <input v-model="form.password" type="password" :class="['lv-input', { err: fieldErrors.password }]"
                 placeholder="비밀번호" @keyup.enter="submit" />
          <span v-if="fieldErrors.password" class="lv-ferr">{{ fieldErrors.password }}</span>
        </div>

        <p v-if="apiError" class="lv-api-err">{{ apiError }}</p>

        <button class="lv-submit" :disabled="loading" @click="submit">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
      </div>

      <p class="lv-link">
        계정이 없으신가요?
        <router-link to="/register">회원가입</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.lv { min-height: 100vh; background: #f8fafc; display: flex; align-items: center; justify-content: center; padding: 24px; }
.lv-card { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,.08); padding: 40px; width: 100%; max-width: 400px; }
.lv-logo { display: flex; align-items: center; gap: 8px; text-decoration: none; margin-bottom: 32px; }
.lv-logo-sq { width: 28px; height: 28px; background: #1e293b; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font: 700 11px 'Inter', sans-serif; }
.lv-logo-nm { font: 600 16px 'Inter', sans-serif; color: #1e293b; }
.lv-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 24px; }
.lv-form { display: flex; flex-direction: column; gap: 12px; }
.lv-field { display: flex; flex-direction: column; gap: 5px; }
.lv-label { font-size: 13px; font-weight: 600; color: #475569; }
.lv-input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 11px 14px; font-size: 14px; color: #1e293b; font-family: inherit; transition: border-color .12s; }
.lv-input:focus { outline: none; border-color: #94a3b8; }
.lv-input.err { border-color: #fca5a5; background: #fff5f5; }
.lv-ferr { font-size: 12px; color: #ef4444; }
.lv-api-err { font-size: 13px; color: #ef4444; padding: 10px 14px; background: #fff5f5; border: 1px solid #fca5a5; border-radius: 8px; white-space: pre-line; }
.lv-submit { margin-top: 8px; padding: 12px; background: #1e293b; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background .15s; }
.lv-submit:hover:not(:disabled) { background: #334155; }
.lv-submit:disabled { opacity: .5; cursor: not-allowed; }
.lv-link { text-align: center; font-size: 13px; color: #94a3b8; margin-top: 24px; }
.lv-link a { color: #3b82f6; text-decoration: none; font-weight: 500; }
.lv-link a:hover { text-decoration: underline; }
</style>
