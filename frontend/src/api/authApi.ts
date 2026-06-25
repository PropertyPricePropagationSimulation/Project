import axios from 'axios'
import { http } from './http'

// 인증이 필요 없는 공개 엔드포인트 전용 인스턴스
// (login/register/logout/checkEmail — 토큰 없이 호출, refresh 루프 방지)
const publicHttp = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export interface TokenResponse {
  accessToken:  string
  refreshToken: string
  expiresIn:    number
}

export interface MemberResponse {
  userId:    number
  email:     string
  nickname:  string
  birthDate: string | null
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await publicHttp.post<TokenResponse>('/auth/login', { email, password })
  return res.data
}

export async function register(
  email: string, password: string, nickname: string, birthDate: string,
): Promise<TokenResponse> {
  const res = await publicHttp.post<TokenResponse>('/auth/register', { email, password, nickname, birthDate })
  return res.data
}

export async function logout(accessToken: string): Promise<void> {
  // 토큰이 만료 상태일 수 있으므로 publicHttp + 수동 헤더 사용 (refresh 루프 방지)
  await publicHttp.post('/auth/logout', null, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
}

export async function getMember(userId: number, accessToken: string): Promise<MemberResponse> {
  // 로그인 직후 호출 — 방금 발급된 토큰이므로 publicHttp + 수동 헤더 사용
  const res = await publicHttp.get<MemberResponse>(`/members/${userId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return res.data
}

export async function checkEmail(email: string): Promise<boolean> {
  const res = await publicHttp.get<boolean>('/members/check-email', { params: { email } })
  return res.data
}

// 인증 필요 — 공유 http 인스턴스 사용 (토큰 자동 첨부 + 만료 시 자동 갱신)
export async function updateMember(
  userId: number,
  payload: { nickname: string; birthDate: string | null },
): Promise<void> {
  await http.put(`/members/${userId}`, payload)
}

export async function changePassword(
  userId: number,
  curPassword: string,
  newPassword: string,
  confirmPassword: string,
): Promise<void> {
  await http.patch(`/members/${userId}/password`, { curPassword, newPassword, confirmPassword })
}

export async function withdrawMember(userId: number): Promise<void> {
  await http.delete(`/members/${userId}`)
}

export function parseUserId(token: string): number | null {
  try {
    const b64 = (token.split('.')[1] ?? '').replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(b64))
    return Number(payload.sub)
  } catch {
    return null
  }
}
