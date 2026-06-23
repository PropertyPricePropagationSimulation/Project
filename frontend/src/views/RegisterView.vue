<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { parseApiError } from '@/api/errorUtils'

const router    = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email:     '',
  password:  '',
  pwConfirm: '',
  nickname:  '',
  birthDate: '',
})

const fieldErrors = reactive({
  email:     '',
  password:  '',
  pwConfirm: '',
  nickname:  '',
  birthDate: '',
})
const apiError = ref('')
const loading  = ref(false)

function validate(): boolean {
  let ok = true

  fieldErrors.email     = ''
  fieldErrors.password  = ''
  fieldErrors.pwConfirm = ''
  fieldErrors.nickname  = ''
  fieldErrors.birthDate = ''
  apiError.value = ''

  if (!form.email) {
    fieldErrors.email = '이메일을 입력해주세요.'
    ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    fieldErrors.email = '올바른 이메일 형식이 아닙니다.'
    ok = false
  }

  if (!form.nickname) {
    fieldErrors.nickname = '닉네임을 입력해주세요.'
    ok = false
  } else if (form.nickname.length < 2) {
    fieldErrors.nickname = '닉네임은 2자 이상이어야 합니다.'
    ok = false
  } else if (form.nickname.length > 20) {
    fieldErrors.nickname = '닉네임은 20자 이하여야 합니다.'
    ok = false
  }

  if (!form.birthDate) {
    fieldErrors.birthDate = '생년월일을 입력해주세요.'
    ok = false
  } else if (new Date(form.birthDate) >= new Date()) {
    fieldErrors.birthDate = '생년월일은 과거 날짜여야 합니다.'
    ok = false
  }

  if (!form.password) {
    fieldErrors.password = '비밀번호를 입력해주세요.'
    ok = false
  } else if (form.password.length < 8) {
    fieldErrors.password = '비밀번호는 8자 이상이어야 합니다.'
    ok = false
  } else if (form.password.length > 100) {
    fieldErrors.password = '비밀번호는 100자 이하여야 합니다.'
    ok = false
  }

  if (!form.pwConfirm) {
    fieldErrors.pwConfirm = '비밀번호를 다시 입력해주세요.'
    ok = false
  } else if (form.password !== form.pwConfirm) {
    fieldErrors.pwConfirm = '비밀번호가 일치하지 않습니다.'
    ok = false
  }

  return ok
}

async function submit() {
  if (!validate()) return
  loading.value = true
  try {
    await authStore.register(form.email, form.password, form.nickname, form.birthDate)
    router.push('/')
  } catch (e) {
    apiError.value = parseApiError(e, '회원가입 중 오류가 발생했습니다.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="rv">
    <div class="rv-card">
      <router-link to="/" class="rv-logo">
        <span class="rv-logo-sq">EF</span>
        <span class="rv-logo-nm">EstateFlow</span>
      </router-link>

      <h1 class="rv-title">회원가입</h1>

      <div class="rv-form">
        <div class="rv-field">
          <label class="rv-label">이메일</label>
          <input v-model="form.email" type="email" :class="['rv-input', { err: fieldErrors.email }]"
                 placeholder="이메일 주소" />
          <span v-if="fieldErrors.email" class="rv-ferr">{{ fieldErrors.email }}</span>
        </div>

        <div class="rv-field">
          <label class="rv-label">닉네임 <span class="rv-hint">2~20자</span></label>
          <input v-model="form.nickname" type="text" :class="['rv-input', { err: fieldErrors.nickname }]"
                 placeholder="닉네임" maxlength="20" />
          <span v-if="fieldErrors.nickname" class="rv-ferr">{{ fieldErrors.nickname }}</span>
        </div>

        <div class="rv-field">
          <label class="rv-label">생년월일</label>
          <input v-model="form.birthDate" type="date" :class="['rv-input', { err: fieldErrors.birthDate }]" />
          <span v-if="fieldErrors.birthDate" class="rv-ferr">{{ fieldErrors.birthDate }}</span>
        </div>

        <div class="rv-field">
          <label class="rv-label">비밀번호 <span class="rv-hint">8~100자</span></label>
          <input v-model="form.password" type="password" :class="['rv-input', { err: fieldErrors.password }]"
                 placeholder="8자 이상" />
          <span v-if="fieldErrors.password" class="rv-ferr">{{ fieldErrors.password }}</span>
        </div>

        <div class="rv-field">
          <label class="rv-label">비밀번호 확인</label>
          <input v-model="form.pwConfirm" type="password" :class="['rv-input', { err: fieldErrors.pwConfirm }]"
                 placeholder="비밀번호 재입력" @keyup.enter="submit" />
          <span v-if="fieldErrors.pwConfirm" class="rv-ferr">{{ fieldErrors.pwConfirm }}</span>
        </div>

        <p v-if="apiError" class="rv-api-err">{{ apiError }}</p>

        <button class="rv-submit" :disabled="loading" @click="submit">
          {{ loading ? '가입 중...' : '회원가입' }}
        </button>
      </div>

      <p class="rv-link">
        이미 계정이 있으신가요?
        <router-link to="/login">로그인</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.rv { min-height: 100vh; background: #f8fafc; display: flex; align-items: center; justify-content: center; padding: 24px; }
.rv-card { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,.08); padding: 40px; width: 100%; max-width: 420px; }
.rv-logo { display: flex; align-items: center; gap: 8px; text-decoration: none; margin-bottom: 32px; }
.rv-logo-sq { width: 28px; height: 28px; background: #1e293b; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font: 700 11px 'Inter', sans-serif; }
.rv-logo-nm { font: 600 16px 'Inter', sans-serif; color: #1e293b; }
.rv-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 24px; }
.rv-form { display: flex; flex-direction: column; gap: 12px; }
.rv-field { display: flex; flex-direction: column; gap: 5px; }
.rv-label { font-size: 13px; font-weight: 600; color: #475569; }
.rv-hint { font-size: 11px; font-weight: 400; color: #94a3b8; margin-left: 4px; }
.rv-input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 11px 14px; font-size: 14px; color: #1e293b; font-family: inherit; transition: border-color .12s; }
.rv-input:focus { outline: none; border-color: #94a3b8; }
.rv-input.err { border-color: #fca5a5; background: #fff5f5; }
.rv-ferr { font-size: 12px; color: #ef4444; }
.rv-api-err { font-size: 13px; color: #ef4444; white-space: pre-line; padding: 10px 14px; background: #fff5f5; border: 1px solid #fca5a5; border-radius: 8px; margin-top: 4px; }
.rv-submit { margin-top: 8px; padding: 12px; background: #1e293b; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background .15s; }
.rv-submit:hover:not(:disabled) { background: #334155; }
.rv-submit:disabled { opacity: .5; cursor: not-allowed; }
.rv-link { text-align: center; font-size: 13px; color: #94a3b8; margin-top: 24px; }
.rv-link a { color: #3b82f6; text-decoration: none; font-weight: 500; }
.rv-link a:hover { text-decoration: underline; }
</style>
