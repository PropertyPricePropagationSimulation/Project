<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { MapEvent } from '@/types/analysis'

const props = defineProps<{
  events: MapEvent[]
  modelValue: number
  windowMonths: 3 | 6 | 12
}>()
const emit = defineEmits<{
  'update:modelValue': [index: number]
  'update:windowMonths': [w: 3 | 6 | 12]
}>()

const WIN = [3, 6, 12] as const

const years = computed(() =>
  [...new Set(props.events.map(e => e.short.slice(0, 4)))].sort()
)
const current = computed(() => props.events[props.modelValue])
const activeYear = computed(() => current.value?.short.slice(0, 4) ?? years.value[0] ?? '')

const yearEvents = computed(() =>
  props.events
    .map((ev, i) => ({ ev, i }))
    .filter(({ ev }) => ev.short.slice(0, 4) === activeYear.value)
)

function goYear(dir: -1 | 1) {
  const i = years.value.indexOf(activeYear.value)
  const ny = years.value[i + dir]
  if (!ny) return
  const first = props.events.findIndex(e => e.short.slice(0, 4) === ny)
  if (first > -1) emit('update:modelValue', first)
}
const canPrev = computed(() => years.value.indexOf(activeYear.value) > 0)
const canNext = computed(() => years.value.indexOf(activeYear.value) < years.value.length - 1)

const open = ref(false)
function jumpYear(y: string) {
  const first = props.events.findIndex(e => e.short.slice(0, 4) === y)
  if (first > -1) emit('update:modelValue', first)
  open.value = false
}

const root = ref<HTMLElement>()
function onDocClick(e: MouseEvent) {
  if (open.value && root.value && !root.value.contains(e.target as Node)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div class="evcluster" ref="root">
    <!-- 연도 -->
    <div class="clseg">
      <span class="cllbl">연도</span>
      <div class="clyear">
        <button class="clarrow" :disabled="!canPrev" @click="goYear(-1)">‹</button>
        <span class="clyr">{{ activeYear }}</span>
        <button class="clarrow" :disabled="!canNext" @click="goYear(1)">›</button>
        <button class="clcaret" @click.stop="open = !open">▾</button>
        <div v-if="open" class="clpop">
          <button
            v-for="y in years" :key="y"
            class="clpop-y" :class="{ on: y === activeYear }"
            @click="jumpYear(y)"
          >{{ y }}</button>
        </div>
      </div>
    </div>

    <div class="cldiv"></div>

    <!-- 그 해 이벤트 칩 -->
    <div class="clseg clev" data-tour="event-select">
      <span class="cllbl">{{ activeYear }}년 이벤트 · {{ yearEvents.length }}건</span>
      <div class="clchips">
        <button
          v-for="{ ev, i } in yearEvents"
          :key="ev.id"
          class="clchip" :class="{ on: i === modelValue }"
          @click="emit('update:modelValue', i)"
        >
          <span class="clchip-ym">{{ parseInt(ev.short.slice(5)) }}월</span>{{ ev.name }}
        </button>
      </div>
    </div>

    <div class="cldiv"></div>

    <!-- 윈도우 -->
    <div class="clseg" data-tour="period-window">
      <span class="cllbl">분석 윈도우</span>
      <div class="clwin">
        <button
          v-for="w in WIN" :key="w"
          :class="{ on: windowMonths === w }"
          @click="emit('update:windowMonths', w)"
        >{{ w }}M</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evcluster { display:flex; align-items:stretch; border:1px solid var(--border2); border-radius:10px; background:var(--w4); position:relative; font-family:'Inter',sans-serif; flex:1; min-width:0; }
.clseg { display:flex; flex-direction:column; gap:4px; justify-content:center; padding:7px 13px; flex-shrink:0; }
.clev { flex:1; min-width:0; }
.cllbl { font-size:9px; font-weight:600; letter-spacing:1px; color:var(--w3); text-transform:uppercase; }
.cldiv { width:1px; background:var(--border2); }

.clyear { display:flex; align-items:center; gap:7px; position:relative; }
.clyr { font:700 15px 'JetBrains Mono',monospace; color:var(--w1); min-width:40px; text-align:center; }
.clarrow { width:24px; height:24px; border-radius:6px; border:1px solid var(--border2); background:var(--w4); color:var(--w2); font-size:12px; cursor:pointer; transition:all .12s; }
.clarrow:hover:not(:disabled) { color:var(--w1); border-color:var(--w3); }
.clarrow:disabled { opacity:.3; cursor:default; }
.clcaret { border:1px solid var(--border2); background:var(--w4); color:var(--w3); font-size:9px; border-radius:5px; padding:3px 6px; cursor:pointer; }

.clchips { display:flex; gap:5px; flex-wrap:wrap; }
.clchip { display:flex; align-items:center; gap:6px; font:500 13px 'Inter',sans-serif; color:var(--w2); border:1px solid var(--border2); background:transparent; padding:4px 11px; border-radius:6px; cursor:pointer; transition:all .12s; white-space:nowrap; }
.clchip:hover { color:var(--w1); border-color:var(--w3); }
.clchip.on { background:var(--w1); color:var(--on-accent); border-color:var(--w1); font-weight:600; }
.clchip-ym { font:600 11px 'JetBrains Mono',monospace; opacity:.55; }

.clwin { display:flex; gap:2px; background:var(--w4); border-radius:6px; padding:2px; }
.clwin button { font:600 11px 'Inter',sans-serif; color:var(--w2); padding:3px 9px; border:0; border-radius:4px; background:none; cursor:pointer; }
.clwin button:hover { color:var(--w1); }
.clwin button.on { background:var(--w1); color:var(--on-accent); }

.clpop { position:absolute; top:calc(100% + 8px); left:0; display:grid; grid-template-columns:repeat(4,1fr); gap:3px; background:var(--glass); border:1px solid var(--border2); border-radius:10px; padding:7px; backdrop-filter:blur(20px); box-shadow:0 14px 44px rgba(0,0,0,.4); z-index:50; }
.clpop-y { font:600 11px 'JetBrains Mono',monospace; color:var(--w2); border:0; background:none; padding:5px 9px; border-radius:5px; cursor:pointer; }
.clpop-y:hover, .clpop-y.on { background:var(--w4); color:var(--w1); }
</style>
