<script setup lang="ts">
import { ref, computed } from 'vue'
import AppHeader from '@/components/common/AppHeader.vue'
import { getAptDeals, type AptDeal } from '@/api/dealsApi'

const REGIONS: Record<string, string> = {
  '11110': '종로구',  '11140': '중구',       '11170': '용산구',
  '11200': '성동구',  '11215': '광진구',     '11230': '동대문구',
  '11260': '중랑구',  '11290': '성북구',     '11305': '강북구',
  '11320': '도봉구',  '11350': '노원구',     '11380': '은평구',
  '11410': '서대문구','11440': '마포구',     '11470': '양천구',
  '11500': '강서구',  '11530': '구로구',     '11545': '금천구',
  '11560': '영등포구','11590': '동작구',     '11620': '관악구',
  '11650': '서초구',  '11680': '강남구',     '11710': '송파구',
  '11740': '강동구',
}

const YEARS  = Array.from({ length: 15 }, (_, i) => 2024 - i)
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
  loading.value  = true
  error.value    = null
  deals.value    = []
  searched.value = true
  try {
    const res    = await getAptDeals(regionCode.value, yearMonth.value)
    deals.value  = res.detail ?? []
  } catch (e: any) {
    error.value = e?.response?.data?.message ?? '조회 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

function fmtAmount(v: number) { return v.toLocaleString() + '만원' }
function fmtDate(d: AptDeal)  { return `${d.dealYear}.${String(d.dealMonth).padStart(2, '0')}.${String(d.dealDay).padStart(2, '0')}` }

const sortKey  = ref<keyof AptDeal>('dealAmount')
const sortDesc = ref(true)

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
    <AppHeader />

    <main class="sv-main">
      <div class="sv-inner">
        <h1 class="sv-title">아파트 매매 거래 조회</h1>

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

        <p v-if="error" class="sv-err">{{ error }}</p>

        <!-- 통계 요약 -->
        <div v-if="deals.length > 0" class="sv-stats">
          <div class="sv-stat">
            <span class="sv-stat-label">조회 건수</span>
            <strong class="sv-stat-value">{{ deals.length }}건</strong>
          </div>
          <div class="sv-stat">
            <span class="sv-stat-label">평균 거래가</span>
            <strong class="sv-stat-value">{{ fmtAmount(Math.round(deals.reduce((s,d) => s + d.dealAmount, 0) / deals.length)) }}</strong>
          </div>
          <div class="sv-stat">
            <span class="sv-stat-label">최고가</span>
            <strong class="sv-stat-value sv-stat-high">{{ fmtAmount(Math.max(...deals.map(d => d.dealAmount))) }}</strong>
          </div>
          <div class="sv-stat">
            <span class="sv-stat-label">최저가</span>
            <strong class="sv-stat-value sv-stat-low">{{ fmtAmount(Math.min(...deals.map(d => d.dealAmount))) }}</strong>
          </div>
        </div>

        <div v-if="loading" class="sv-skeleton-wrap">
          <div class="sv-skeleton" v-for="i in 8" :key="i" />
        </div>

        <div v-else-if="deals.length > 0" class="sv-table-wrap">
          <table class="sv-table">
            <thead>
              <tr>
                <th @click="toggleSort('aptName')">아파트명</th>
                <th @click="toggleSort('dong')">법정동</th>
                <th @click="toggleSort('dealAmount')">거래금액 {{ sortKey === 'dealAmount' ? (sortDesc ? '▼' : '▲') : '' }}</th>
                <th @click="toggleSort('area')">면적(㎡) {{ sortKey === 'area' ? (sortDesc ? '▼' : '▲') : '' }}</th>
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
          <div class="sv-empty-icon">🔍</div>
          <p>{{ REGIONS[regionCode] }} {{ year }}년 {{ month }}월</p>
          <p class="sv-empty-sub">조회된 거래 내역이 없습니다.</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.sv { min-height: 100vh; background: #f8fafc; }

.sv-main { padding: 40px 24px; }
.sv-inner { max-width: 1100px; margin: 0 auto; }
.sv-title { font-size: 22px; font-weight: 700; color: #1e293b; margin-bottom: 24px; }

.sv-filter { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.sv-sel { background: #fff; border: 1px solid #e2e8f0; color: #1e293b; padding: 8px 12px; border-radius: 6px; font-size: 14px; cursor: pointer; font-family: inherit; }
.sv-sel:focus { outline: none; border-color: #94a3b8; }
.sv-btn { background: #1e293b; border: none; color: #fff; padding: 8px 24px; border-radius: 6px; font-size: 14px; cursor: pointer; font-weight: 500; transition: background .15s; font-family: inherit; }
.sv-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sv-btn:hover:not(:disabled) { background: #334155; }

.sv-err { color: #ef4444; font-size: 13px; margin-bottom: 12px; }
.sv-result-info { font-size: 13px; color: #64748b; margin-bottom: 12px; }

.sv-table-wrap { overflow-x: auto; background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.sv-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.sv-table th { background: #f8fafc; padding: 12px 16px; text-align: left; color: #64748b; font-weight: 600; font-size: 13px; border-bottom: 1px solid #e2e8f0; cursor: pointer; user-select: none; white-space: nowrap; }
.sv-table th:hover { color: #1e293b; }
.sv-table td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; color: #334155; }
.sv-table tr:last-child td { border-bottom: none; }
.sv-table tr:hover td { background: #f8fafc; }
.sv-amt { color: #3b82f6; font-weight: 500; }

/* 통계 */
.sv-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.sv-stat { background: #fff; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.sv-stat-label { display: block; font-size: 11px; color: #94a3b8; font-weight: 500; margin-bottom: 4px; }
.sv-stat-value { font-size: 16px; font-weight: 700; color: #1e293b; }
.sv-stat-high { color: #3b82f6; }
.sv-stat-low { color: #64748b; }

/* 스켈레톤 */
.sv-skeleton-wrap { background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.sv-skeleton { height: 52px; background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-bottom: 1px solid #f8fafc; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

.sv-empty { text-align: center; padding: 60px 0; background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.sv-empty-icon { font-size: 36px; margin-bottom: 12px; }
.sv-empty p { font-size: 14px; color: #475569; font-weight: 500; }
.sv-empty-sub { font-size: 13px; color: #94a3b8; margin-top: 4px; font-weight: 400; }
</style>
