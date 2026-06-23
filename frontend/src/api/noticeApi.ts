import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

export interface Notice {
  noticeId:  number
  title:     string
  writer:    string
  content:   string
  createdAt: string
  updatedAt: string
}

export interface PageResponse<T> {
  content:    T[]
  page:       number
  size:       number
  totalCount: number
}

export async function getNotices(page = 1, size = 5): Promise<PageResponse<Notice>> {
  const res = await http.get<PageResponse<Notice>>('/notices', { params: { page, size } })
  return res.data
}

export async function getNotice(id: number): Promise<Notice> {
  const res = await http.get<Notice>(`/notices/${id}`)
  return res.data
}
