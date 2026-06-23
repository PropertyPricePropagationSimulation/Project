import axios from 'axios'
import type { BaseResponse } from '@/types/analysis'

const http = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 35_000,
})

export interface AptDeal {
  regionCode: string
  dong:       string
  aptName:    string
  jibun:      string
  dealYear:   number
  dealMonth:  number
  dealDay:    number
  area:       number
  floor:      number
  dealAmount: number
  buildYear:  number
}

export async function getAptDeals(
  regionCode: string,
  yearMonth: string,
): Promise<BaseResponse<AptDeal[]>> {
  const res = await http.get<BaseResponse<AptDeal[]>>('/deals/apt', {
    params: { regionCode, yearMonth },
  })
  return res.data
}
