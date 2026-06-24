import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout, getMember, parseUserId, register as apiRegister } from '@/api/authApi'

export const useAuthStore = defineStore('auth', () => {
  const accessToken  = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const nickname     = ref<string | null>(localStorage.getItem('nickname'))

  // http.ts의 토큰 갱신 성공 이벤트를 받아 ref 동기화
  window.addEventListener('auth:refreshed', (e: Event) => {
    accessToken.value = (e as CustomEvent<string>).detail
  })

  const isLoggedIn = computed(() => !!accessToken.value)

  const isAdmin = computed(() => {
    if (!accessToken.value) return false
    try {
      const b64 = (accessToken.value.split('.')[1] ?? '').replace(/-/g, '+').replace(/_/g, '/')
      const payload = JSON.parse(atob(b64))
      return payload.role === 'ADMIN'
    } catch { return false }
  })

  function _persist(at: string, rt: string, nick: string) {
    accessToken.value  = at
    refreshToken.value = rt
    nickname.value     = nick
    localStorage.setItem('access_token',  at)
    localStorage.setItem('refresh_token', rt)
    localStorage.setItem('nickname',      nick)
  }

  function _clear() {
    accessToken.value  = null
    refreshToken.value = null
    nickname.value     = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('nickname')
  }

  async function login(email: string, password: string) {
    const tokens = await apiLogin(email, password)
    const userId = parseUserId(tokens.accessToken)
    const member = userId ? await getMember(userId, tokens.accessToken) : null
    _persist(tokens.accessToken, tokens.refreshToken, member?.nickname ?? email)
  }

  async function register(email: string, password: string, nick: string, birthDate: string) {
    const tokens = await apiRegister(email, password, nick, birthDate)
    _persist(tokens.accessToken, tokens.refreshToken, nick)
  }

  async function logout() {
    if (accessToken.value) {
      try { await apiLogout(accessToken.value) } catch { /* ignore */ }
    }
    _clear()
  }

  return { accessToken, nickname, isLoggedIn, isAdmin, login, register, logout }
})
