<script setup lang="ts">
import type { MapEvent } from '@/types/analysis'

defineProps<{
  events: MapEvent[]
  modelValue: number
}>()

const emit = defineEmits<{
  'update:modelValue': [index: number]
}>()
</script>

<template>
  <div class="evs">
    <button
      v-for="(ev, i) in events"
      :key="i"
      class="evb"
      :class="{ on: i === modelValue }"
      @click="emit('update:modelValue', i)"
    >{{ ev.short }} {{ ev.name }}</button>
  </div>
</template>
