import axios from 'axios'
import type { PageResponse } from '@/api/noticeApi'
import { useAuthStore } from '@/stores/authStore'

const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

http.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

export interface Qna {
  qnaId:     number
  title:     string
  writerId:  number
  writer:    string
  content:   string
  answered:  boolean
  createdAt: string
  updatedAt: string
}

export interface QnaComment {
  commentId: number
  qnaId:     number
  content:   string
  writer:    string
  writerId:  number
  createdAt: string
  updatedAt: string
}

export const getQnas    = (page = 1, size = 10) =>
  http.get<PageResponse<Qna>>('/qnas', { params: { page, size } }).then(r => r.data)

export const getQna     = (id: number) =>
  http.get<Qna>(`/qnas/${id}`).then(r => r.data)

export const createQna  = (title: string, content: string) =>
  http.post('/qnas', { title, content })

export const deleteQna  = (id: number) =>
  http.delete(`/qnas/${id}`)

export const getComments   = (qnaId: number) =>
  http.get<QnaComment[]>(`/qnas/${qnaId}/comments`).then(r => r.data)

export const createComment = (qnaId: number, content: string) =>
  http.post(`/qnas/${qnaId}/comments`, { content })

export const deleteComment = (qnaId: number, commentId: number) =>
  http.delete(`/qnas/${qnaId}/comments/${commentId}`)
