<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getAptDeals, type AptDeal } from '@/api/dealsApi'

const router = useRouter()

const REGIONS: Record<string, string> = {
  '11110': '종로구', '11140': '중구',      '11170': '용산구',
  '11200': '성동구', '11215': '광진구',    '11230': '동대문구',
  '11260': '중랑구', '11290': '성북구',    '11305': '강북구',
  '11320': '도봉구', '11350': '노원구',    '11380': '은평구',
  '11410': '서대문구','11440': '마포구',   '11470': '양천구',
  '11500': '강서구', '11530': '구로구',    '11545': '금천구',
  '11560': '영등포구','11590': '동작구',   '11620': '관악구',
  '11650': '서초구', '11680': '강남구',    '11710': '송파구',
  '11740': '강동구',
}

const YEARS = Array.from({ length: 15 }, (_, i) => 2024 - i)
const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1)

const regionCode = ref('11680')
const year       = ref(2024)
const month      = ref(new Date().getMonth() + 1)
const deals      = ref<AptDeal[]>([])
const loading    = ref(false)
const error      = ref<string | null>(null)
const searched   = ref(false)

const yearMonth = computed(() =>
  `${year.value}${String(month.value).padStart(2, '0')}`,
)

async function search() {
  loading.value = true
  error.value   = null
  deals.value   = []
  searched.value = true
  try {
    const res = await getAptDeals(regionCode.value, yearMonth.value)
    deals.value = res.detail ?? []
  } catch (e: any) {
    error.value = e?.response?.data?.message ?? '조회 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

function fmtAmount(v: number) {
  return v.toLocaleString() + '만원'
}

function fmtDate(d: AptDeal) {
  return `${d.dealYear}.${String(d.dealMonth).padStart(2, '0')}.${String(d.dealDay).padStart(2, '0')}`
}

const sortKey   = ref<keyof AptDeal>('dealAmount')
const sortDesc  = ref(true)

function toggleSort(key: keyof AptDeal) {
  if (sortKey.value === key) sortDesc.value = !sortDesc.value
  else { sortKey.value = key; sortDesc.value = true }
}

const sorted = computed(() => {
  const arr = [...deals.value]
  arr.sort((a, b) => {
    const va = a[sortKey.value] as number | string
    const vb = b[sortKey.value] as number | string
    return sortDesc.value ? (va < vb ? 1 : -1) : (va > vb ? 1 : -1)
  })
  return arr
})
</script>

<template>
  <div class="sv">
    <div class="sv-hdr">
      <button class="sv-back" @click="router.back()">← 돌아가기</button>
      <span class="sv-title">아파트 매매 거래 조회</span>
    </div>

    <div class="sv-filter">
      <select v-model="regionCode" class="sv-sel">
        <option v-for="(name, code) in REGIONS" :key="code" :value="code">
          {{ name }}
        </option>
      </select>

      <select v-model="year" class="sv-sel">
        <option v-for="y in YEARS" :key="y" :value="y">{{ y }}년</option>
      </select>

      <select v-model="month" class="sv-sel">
        <option v-for="m in MONTHS" :key="m" :value="m">{{ m }}월</option>
      </select>

      <button class="sv-btn" :disabled="loading" @click="search">
        {{ loading ? '조회 중...' : '조회' }}
      </button>
    </div>

    <div v-if="error" class="sv-err">{{ error }}</div>

    <div v-if="searched && !loading" class="sv-result-info">
      {{ REGIONS[regionCode] }} {{ year }}년 {{ month }}월 —
      <strong>{{ deals.length }}건</strong>
    </div>

    <div v-if="deals.length > 0" class="sv-table-wrap">
      <table class="sv-table">
        <thead>
          <tr>
            <th @click="toggleSort('aptName')">아파트명</th>
            <th @click="toggleSort('dong')">법정동</th>
            <th @click="toggleSort('dealAmount')">거래금액 {{ sortKey==='dealAmount' ? (sortDesc?'▼':'▲') : '' }}</th>
            <th @click="toggleSort('area')">면적(㎡) {{ sortKey==='area' ? (sortDesc?'▼':'▲') : '' }}</th>
            <th @click="toggleSort('floor')">층</th>
            <th @click="toggleSort('dealYear')">거래일</th>
            <th @click="toggleSort('buildYear')">건축년도</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(d, i) in sorted" :key="i">
            <td>{{ d.aptName }}</td>
            <td>{{ d.dong }}</td>
            <td class="sv-amt">{{ fmtAmount(d.dealAmount) }}</td>
            <td>{{ d.area }}</td>
            <td>{{ d.floor }}</td>
            <td>{{ fmtDate(d) }}</td>
            <td>{{ d.buildYear }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="searched && !loading" class="sv-empty">
      조회된 거래 내역이 없습니다.
    </div>
  </div>
</template>

<style scoped>
.sv { min-height: 100vh; background: #0a0c10; color: #e2e8f0; padding: 24px; font-family: 'Noto Sans KR', sans-serif; }

.sv-hdr { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.sv-back { background: none; border: 1px solid #334155; color: #94a3b8; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.sv-back:hover { color: #e2e8f0; border-color: #64748b; }
.sv-title { font-size: 18px; font-weight: 600; color: #f1f5f9; }

.sv-filter { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.sv-sel { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; padding: 8px 12px; border-radius: 6px; font-size: 14px; cursor: pointer; }
.sv-btn { background: #3b82f6; border: none; color: #fff; padding: 8px 24px; border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 500; }
.sv-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sv-btn:hover:not(:disabled) { background: #2563eb; }

.sv-err { color: #f87171; font-size: 13px; margin-bottom: 12px; }
.sv-result-info { font-size: 13px; color: #94a3b8; margin-bottom: 12px; }

.sv-table-wrap { overflow-x: auto; }
.sv-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.sv-table th { background: #1e293b; padding: 10px 14px; text-align: left; color: #94a3b8; font-weight: 500; border-bottom: 1px solid #334155; cursor: pointer; user-select: none; white-space: nowrap; }
.sv-table th:hover { color: #e2e8f0; }
.sv-table td { padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
.sv-table tr:hover td { background: #1e293b; }
.sv-amt { color: #60a5fa; font-weight: 500; }

.sv-empty { text-align: center; color: #475569; padding: 60px 0; font-size: 14px; }
</style>
