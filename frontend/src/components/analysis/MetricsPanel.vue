<script setup lang="ts">
import { computed } from 'vue'
import type { District } from '@/types/analysis'

const props = defineProps<{
  districts: District[]
  curMonth: number
}>()

function valToColor(v: number): string {
  if (v >= 15) return '#ff1133'
  if (v >= 10) return '#ff6622'
  if (v >= 5)  return '#ffcc22'
  if (v >= 0)  return '#334466'
  if (v >= -5) return '#2255cc'
  return '#1133aa'
}

const maxChange    = computed(() => Math.max(...props.districts.map(d => d.change)))
const maxDistrict  = computed(() => props.districts.find(d => d.change === maxChange.value))
const activeCount  = computed(() => props.districts.filter(d => (props.curMonth - 3) >= d.lag).length)
const top5         = computed(() => [...props.districts].sort((a, b) => a.lag - b.lag).slice(0, 5))
const top5MaxChange = computed(() => Math.max(...top5.value.map(d => d.change)))
</script>

<template>
  <div class="rp">
    <div class="mc">
      <div class="mc-l">최대 변화율</div>
      <div class="mc-v" style="color:#ff4d6d">+{{ maxChange.toFixed(1) }}%</div>
      <div class="mc-s">{{ maxDistrict?.name ?? '—' }} 기준</div>
    </div>
    <div class="mc">
      <div class="mc-l">반응 지역 수</div>
      <div class="mc-v" style="color:rgba(255,255,255,.75)">{{ activeCount }}</div>
      <div class="mc-s">현재 시점 기준</div>
    </div>
    <div class="leg">
      <div class="mc-l">변화율</div>
      <div class="leg-r"><div class="leg-sw" style="background:#ff1133"></div>+15% 이상</div>
      <div class="leg-r"><div class="leg-sw" style="background:#ff6622"></div>+10~15%</div>
      <div class="leg-r"><div class="leg-sw" style="background:#ffcc22"></div>+5~10%</div>
      <div class="leg-r"><div class="leg-sw" style="background:#334466"></div>±5%</div>
      <div class="leg-r"><div class="leg-sw" style="background:#2255cc"></div>-5% 이하</div>
    </div>
    <div class="tp">
      <div class="tp-t">반응 순위 TOP 5</div>
      <div v-for="d in top5" :key="d.name" class="tp-row">
        <div class="tp-nm">{{ d.name }}</div>
        <div class="tp-right">
          <div class="tp-bar">
            <div
              class="tp-bf"
              :style="{
                width: top5MaxChange !== 0 ? (d.change / top5MaxChange * 100).toFixed(0) + '%' : '0%',
                background: valToColor(d.change),
              }"
            ></div>
          </div>
          <div class="tp-pct" :style="{ color: valToColor(d.change) }">
            {{ d.change >= 0 ? '+' : '' }}{{ d.change.toFixed(1) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
