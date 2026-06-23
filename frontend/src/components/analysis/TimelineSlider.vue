<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { MapEvent } from '@/types/analysis'

const props = defineProps<{
  months: string[]
  modelValue: number
  playing: boolean
  currentEvent: MapEvent | undefined
}>()

const emit = defineEmits<{
  'update:modelValue': [month: number]
  'update:playing':   [playing: boolean]
}>()

const trackRef = ref<HTMLDivElement>()
let sliderDrag = false
let ptimer: ReturnType<typeof setInterval> | null = null
const cleanupFns: (() => void)[] = []

const sliderPct = computed(() => props.modelValue / (props.months.length - 1) * 100)

const timelineLabel = computed(() => {
  if (!props.currentEvent) return '—'
  const off = props.modelValue - 3
  if (off === 0) return props.currentEvent.short + ' — 이벤트 발생'
  if (off > 0)   return props.currentEvent.short + ' → +' + off + '개월'
  return props.currentEvent.short + ' → ' + off + '개월'
})

// T+0 위치 (index 3)를 퍼센트로 고정 표시
const eventMarkPct = computed(() => (3 / (props.months.length - 1) * 100).toFixed(2) + '%')

function monthFromX(cx: number): number {
  if (!trackRef.value) return props.modelValue
  const r = trackRef.value.getBoundingClientRect()
  return Math.max(0, Math.min(props.months.length - 1, Math.round((cx - r.left) / r.width * (props.months.length - 1))))
}

function stopPlay() {
  if (ptimer) { clearInterval(ptimer); ptimer = null }
  emit('update:playing', false)
}

function togglePlay() {
  if (props.playing) {
    stopPlay()
  } else {
    emit('update:playing', true)
    ptimer = setInterval(() => {
      if (props.modelValue < props.months.length - 1) {
        emit('update:modelValue', props.modelValue + 1)
      } else {
        stopPlay()
      }
    }, 800)
  }
}

function startThumbDrag() { sliderDrag = true }

onMounted(() => {
  const track = trackRef.value!

  track.addEventListener('mousedown', e => {
    sliderDrag = true
    emit('update:modelValue', monthFromX(e.clientX))
    e.preventDefault()
  })

  const onMouseMove = (e: MouseEvent) => {
    if (sliderDrag) emit('update:modelValue', monthFromX(e.clientX))
  }
  const onMouseUp = () => { sliderDrag = false }
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)

  const onTouchMove = (e: TouchEvent) => {
    if (sliderDrag && e.touches[0]) emit('update:modelValue', monthFromX(e.touches[0].clientX))
  }
  const onTouchEnd = () => { sliderDrag = false }
  track.addEventListener('touchstart', e => {
    sliderDrag = true
    if (e.touches[0]) emit('update:modelValue', monthFromX(e.touches[0].clientX))
    e.preventDefault()
  }, { passive: false })
  window.addEventListener('touchmove', onTouchMove, { passive: false })
  window.addEventListener('touchend', onTouchEnd)

  cleanupFns.push(
    () => window.removeEventListener('mousemove', onMouseMove),
    () => window.removeEventListener('mouseup', onMouseUp),
    () => window.removeEventListener('touchmove', onTouchMove),
    () => window.removeEventListener('touchend', onTouchEnd),
  )
})

onUnmounted(() => {
  if (ptimer) clearInterval(ptimer)
  cleanupFns.forEach(fn => fn())
})
</script>

<template>
  <div class="bot">
    <div class="bt-top">
      <div class="bt-l">Event Timeline</div>
      <div class="bt-c">{{ timelineLabel }}</div>
      <div class="ctrl">
        <button class="cb" @click="emit('update:modelValue', 0)">«</button>
        <button class="cb" @click="emit('update:modelValue', Math.max(0, modelValue - 1))">‹</button>
        <button class="cb" :class="{ on: playing }" @click="togglePlay">{{ playing ? '⏸' : '▶' }}</button>
        <button class="cb" @click="emit('update:modelValue', Math.min(months.length - 1, modelValue + 1))">›</button>
        <button class="cb" @click="emit('update:modelValue', months.length - 1)">»</button>
      </div>
    </div>
    <div class="str" ref="trackRef">
      <div class="stl"></div>
      <div class="stf" :style="{ width: sliderPct + '%' }"></div>
      <div class="sth" :style="{ left: sliderPct + '%' }" @mousedown.stop.prevent="startThumbDrag"></div>
    </div>
    <div class="tick-area">
      <div class="trow">
        <span v-for="(m, i) in months" :key="i" class="tk" :class="{ on: i === modelValue }">{{ m }}</span>
      </div>
      <div class="ev-mark" :style="{ left: eventMarkPct, transform: 'translateX(-50%)' }">
        <div class="em-dot"></div>
        <div class="em-line"></div>
      </div>
    </div>
  </div>
</template>
