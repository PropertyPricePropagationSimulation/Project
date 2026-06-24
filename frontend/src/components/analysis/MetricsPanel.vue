<script setup lang="ts">
import { ref, computed } from 'vue'
import type { RegionResult } from '@/types/analysis'
import { LAWD_CD_TO_NAME } from '@/constants/regionCodes'
import { valToColor } from '@/utils/colorScale'

const props = defineProps<{
  regions: RegionResult[]
  currentRelativeMonth: number
}>()

function monthlyChange(r: RegionResult): number {
  const md = r.monthly.find(m => m.relative_month === props.currentRelativeMonth)
  return md?.price_change_from_event_pct ?? 0
}

function isActive(r: RegionResult): boolean {
  const lag = r.window_summary.lag_months
  return lag !== null && props.currentRelativeMonth >= lag
}

function regionName(r: RegionResult): string {
  return LAWD_CD_TO_NAME[r.dong_code] ?? r.dong_code
}

const activeCount = computed(() => props.regions.filter(isActive).length)

const maxRegion = computed(() =>
  props.regions.length === 0
    ? null
    : props.regions.reduce((mx, r) => monthlyChange(r) > monthlyChange(mx) ? r : mx)
)
const maxChange = computed(() => maxRegion.value ? monthlyChange(maxRegion.value) : 0)

const top5 = computed(() =>
  [...props.regions]
    .sort((a, b) => (a.window_summary.lag_months ?? 99) - (b.window_summary.lag_months ?? 99))
    .slice(0, 5)
)
const top5Max = computed(() =>
  Math.max(...top5.value.map(r => Math.abs(monthlyChange(r))), 0.1)
)

// ── 사이즈 제어 ──────────────────────────────────────────────────────────────
const size = ref<0 | 1 | 2>(0)

const SIZES = [
  { rp: '170px', pad: '10px 12px', mcl: '8px',   mcv: '20px', mcs: '9px',   tpt: '8px',  tpnm: '10.5px', tppct: '9.5px',  legr: '9.5px'  },
  { rp: '212px', pad: '12px 14px', mcl: '9.5px', mcv: '24px', mcs: '10.5px',tpt: '9px',  tpnm: '12px',   tppct: '11px',   legr: '11px'   },
  { rp: '258px', pad: '14px 16px', mcl: '11px',  mcv: '29px', mcs: '12px',  tpt: '10px', tpnm: '13.5px', tppct: '12.5px', legr: '12.5px' },
] as const

function decreaseSize() {
  if (size.value > 0) {
    size.value = (size.value - 1) as 0 | 1 | 2
  }
}

function increaseSize() {
  if (size.value < 2) {
    size.value = (size.value + 1) as 0 | 1 | 2
  }
}

const sz = computed(() => SIZES[size.value])
</script>

<template>
  <div class="rp-wrap">
    <div class="rp" :style="{ width: sz.rp }">

    <div class="mc" :style="{ padding: sz.pad }">
      <div class="mc-l" :style="{ fontSize: sz.mcl }">현재 최대 변화율</div>
      <div class="mc-v" :style="{ color: maxChange >= 0 ? '#ff4d6d' : '#4d9fff', fontSize: sz.mcv }">
        {{ maxChange >= 0 ? '+' : '' }}{{ maxChange.toFixed(1) }}%
      </div>
      <div class="mc-s" :style="{ fontSize: sz.mcs }">{{ maxRegion ? regionName(maxRegion) : '—' }} 기준</div>
    </div>

    <div class="mc" :style="{ padding: sz.pad }">
      <div class="mc-l" :style="{ fontSize: sz.mcl }">반응 지역 수</div>
      <div class="mc-v" :style="{ fontSize: sz.mcv, color: 'rgba(255,255,255,.75)' }">
        {{ activeCount }}<span :style="{ fontSize: sz.mcs, color: 'var(--w3)' }"> / {{ regions.length }}</span>
      </div>
      <div class="mc-s" :style="{ fontSize: sz.mcs }">현재 시점 기준</div>
    </div>

    <div class="leg" :style="{ padding: sz.pad }">
      <div class="mc-l" :style="{ fontSize: sz.mcl }">변화율</div>
      <div class="leg-r" :style="{ fontSize: sz.legr }"><div class="leg-sw" style="background:#ff1133"></div>+15% 이상</div>
      <div class="leg-r" :style="{ fontSize: sz.legr }"><div class="leg-sw" style="background:#ff6622"></div>+10~15%</div>
      <div class="leg-r" :style="{ fontSize: sz.legr }"><div class="leg-sw" style="background:#ffcc22"></div>+5~10%</div>
      <div class="leg-r" :style="{ fontSize: sz.legr }"><div class="leg-sw" style="background:#334466"></div>±5%</div>
      <div class="leg-r" :style="{ fontSize: sz.legr }"><div class="leg-sw" style="background:#2255cc"></div>-5% 이하</div>
    </div>

    <div class="tp" :style="{ padding: sz.pad }">
      <div class="tp-t" :style="{ fontSize: sz.tpt }">빠른 반응 TOP 5</div>
      <template v-if="regions.length > 0">
        <div v-for="r in top5" :key="r.dong_code" class="tp-row">
          <div class="tp-nm" :style="{ fontSize: sz.tpnm }">{{ regionName(r) }}</div>
          <div class="tp-right">
            <div class="tp-bar">
              <div
                class="tp-bf"
                :style="{
                  width: (Math.abs(monthlyChange(r)) / top5Max * 100).toFixed(0) + '%',
                  background: valToColor(monthlyChange(r)),
                }"
              ></div>
            </div>
            <div class="tp-pct" :style="{ fontSize: sz.tppct, color: valToColor(monthlyChange(r)) }">
              {{ monthlyChange(r) >= 0 ? '+' : '' }}{{ monthlyChange(r).toFixed(1) }}%
            </div>
          </div>
        </div>
      </template>
      <div v-else class="tp-empty">데이터 로딩 중...</div>
    </div>

    </div><!-- /.rp -->

    <!-- 사이즈 컨트롤: 플로팅과 타임라인 사이 -->
    <div class="rp-szctrl">
      <button class="rp-sz" :disabled="size === 0" @click="decreaseSize">−</button>
      <button class="rp-sz" :disabled="size === 2" @click="increaseSize">+</button>
    </div>

  </div><!-- /.rp-wrap -->
</template>

<style scoped>
.rp-szctrl {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  flex-shrink: 0;
  pointer-events: auto;
}
.rp-sz {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(255,255,255,.04);
  color: rgba(255,255,255,.45);
  font-size: 13px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .12s;
  font-family: 'Inter', sans-serif;
  padding: 0;
}
.rp-sz:hover:not(:disabled) {
  border-color: rgba(255,255,255,.3);
  color: rgba(255,255,255,.85);
  background: rgba(255,255,255,.08);
}
.rp-sz:disabled {
  opacity: 0.25;
  cursor: default;
}
</style>
