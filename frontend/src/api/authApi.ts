import axios from 'axios'

const http = axios.create({
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
  userId:   number
  email:    string
  nickname: string
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await http.post<TokenResponse>('/auth/login', { email, password })
  return res.data
}

export async function register(
  email: string, password: string, nickname: string, birthDate: string,
): Promise<TokenResponse> {
  const res = await http.post<TokenResponse>('/auth/register', { email, password, nickname, birthDate })
  return res.data
}

export async function logout(accessToken: string): Promise<void> {
  await http.post('/auth/logout', null, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
}

export async function getMember(userId: number, accessToken: string): Promise<MemberResponse> {
  const res = await http.get<MemberResponse>(`/members/${userId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return res.data
}

export function parseUserId(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return Number(payload.sub)
  } catch {
    return null
  }
}
