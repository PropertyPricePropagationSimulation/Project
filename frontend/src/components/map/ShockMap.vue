<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { District } from '@/types/analysis'

const props = defineProps<{
  districts: District[]
  curMonth: number
  showLabels: boolean
}>()

const LERP = 0.07
let map: mapboxgl.Map | null = null
let baseGeoJSON: Record<string, unknown> | null = null
let mapLoaded = false
let animId: number | null = null
const dispVals: Record<string, number> = {}
const districtMap: Record<string, District> = {}

function buildDistrictMap() {
  Object.keys(districtMap).forEach(k => delete districtMap[k])
  props.districts.forEach(d => { districtMap[d.name] = d })
}

function valToColor(v: number): string {
  if (v >= 15) return '#ff1133'
  if (v >= 10) return '#ff6622'
  if (v >= 5)  return '#ffcc22'
  if (v >= 0)  return '#334466'
  if (v >= -5) return '#2255cc'
  return '#1133aa'
}

function getTarget(name: string): number {
  const d = districtMap[name]
  if (!d) return 0
  const ms = props.curMonth - 3
  if (ms < d.lag) return 0
  return d.change * Math.min(1, (ms - d.lag + 1) / 2.0)
}

function pushMapData() {
  if (!baseGeoJSON || !map) return
  const features = (baseGeoJSON.features as Array<Record<string, unknown>>).map(f => {
    const p    = f.properties as Record<string, unknown>
    const name = p.name as string
    const d    = districtMap[name]
    const v    = dispVals[name] ?? 0
    const col  = valToColor(v)
    return {
      ...f,
      properties: {
        ...p,
        value:      v,
        height:     Math.max(0, v) * 200,
        base:       0,
        fillColor:  col,
        labelColor: Math.abs(v) > 2 ? col : 'rgba(255,255,255,0.4)',
        active:     d ? ((props.curMonth - 3) >= d.lag ? 1 : 0) : 0,
      },
    }
  })
  const src = map.getSource('districts') as mapboxgl.GeoJSONSource | undefined
  if (src) src.setData({ type: 'FeatureCollection', features } as unknown as Parameters<typeof src.setData>[0])
}

function startAnim() {
  if (animId !== null) cancelAnimationFrame(animId)
  function loop() {
    let moved = false
    props.districts.forEach(d => {
      const target = getTarget(d.name)
      const cur    = dispVals[d.name] ?? 0
      const diff   = target - cur
      if (Math.abs(diff) > 0.01 && (props.curMonth - 3) >= d.lag) {
        dispVals[d.name] = cur + diff * LERP
        moved = true
      } else if (cur !== target) {
        dispVals[d.name] = target
        moved = true
      }
    })
    if (moved && mapLoaded) pushMapData()
    animId = requestAnimationFrame(loop)
  }
  loop()
}

function setProgress(pct: number, txt: string) {
  const fill = document.getElementById('ldFill')
  const text = document.getElementById('ldTxt')
  if (fill) fill.style.width = pct + '%'
  if (text) text.textContent = txt
}

async function loadGeoJSON(): Promise<Record<string, unknown>> {
  setProgress(20, '서울 행정구역 로딩...')
  const geo = await (await fetch('/geojson/seoul.json')).json() as Record<string, unknown>
  setProgress(80, '데이터 연결 중...')
  const TARGET_NAMES = new Set(props.districts.map(d => d.name))
  const features = (geo.features as Array<{ properties: { name: string } }>)
    .filter(f => TARGET_NAMES.has(f.properties.name))
  setProgress(90, '지도 레이어 생성...')
  return { type: 'FeatureCollection', features }
}

// 라벨 visibility
watch(() => props.showLabels, val => {
  if (mapLoaded && map) {
    map.setLayoutProperty('districts-labels', 'visibility', val ? 'visible' : 'none')
  }
})

// districts 교체 시 dispVals 리셋 (이벤트 전환 또는 API 결과 반영)
watch(() => props.districts, newDistricts => {
  buildDistrictMap()
  newDistricts.forEach(d => { dispVals[d.name] = 0 })
})

onMounted(() => {
  buildDistrictMap()
  props.districts.forEach(d => { dispVals[d.name] = 0 })

  mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN as string

  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [127.02, 37.52],
    zoom: 10.2,
    pitch: 55,
    bearing: -10,
    antialias: true,
  })

  map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), 'bottom-right')

  map.on('load', async () => {
    try {
      baseGeoJSON = await loadGeoJSON()

      const feats = baseGeoJSON.features as Array<Record<string, unknown>>
      baseGeoJSON.features = feats.map(f => ({
        ...f,
        properties: {
          ...(f.properties as object),
          value: 0, height: 0, base: 0,
          fillColor:  '#223344',
          labelColor: 'rgba(255,255,255,0.4)',
          active: 0,
        },
      }))

      map!.addSource('districts', {
        type: 'geojson',
        data: baseGeoJSON as unknown as mapboxgl.GeoJSONSourceSpecification['data'],
      })

      map!.addLayer({
        id: 'districts-3d',
        type: 'fill-extrusion',
        source: 'districts',
        paint: {
          'fill-extrusion-color':   ['get', 'fillColor'],
          'fill-extrusion-height':  ['get', 'height'],
          'fill-extrusion-base':    ['get', 'base'],
          'fill-extrusion-opacity': 0.82,
        },
      })

      map!.addLayer({
        id: 'districts-line',
        type: 'line',
        source: 'districts',
        paint: { 'line-color': 'rgba(255,255,255,0.1)', 'line-width': 0.7 },
      })

      map!.addLayer({
        id: 'districts-labels',
        type: 'symbol',
        source: 'districts',
        layout: {
          'text-field':         ['get', 'name'],
          'text-font':          ['Open Sans Semibold', 'Arial Unicode MS Bold'],
          'text-size':          ['interpolate', ['linear'], ['zoom'], 9, 9, 12, 12],
          'text-offset':        [0, 0],
          'text-anchor':        'center',
          'text-allow-overlap': false,
        },
        paint: {
          'text-color':      ['get', 'labelColor'],
          'text-halo-color': 'rgba(0,0,0,0.7)',
          'text-halo-width': 1.5,
        },
      })

      // hover 툴팁 — DOM 직접 조작 (Mapbox 이벤트는 Vue 반응형 밖에서 실행)
      map!.on('mousemove', 'districts-3d', e => {
        map!.getCanvas().style.cursor = 'pointer'
        const feature = e.features?.[0] as unknown as { properties: Record<string, unknown> } | undefined
        if (!feature) return
        const name = feature.properties.name as string
        const d = districtMap[name]
        if (!d) return
        const v   = dispVals[name] ?? 0
        const col = valToColor(d.change)
        const act = (props.curMonth - 3) >= d.lag

        const ttName = document.getElementById('ttName')
        if (ttName) { ttName.textContent = name; ttName.style.color = col }
        const ttChange = document.getElementById('ttChange')
        if (ttChange) ttChange.textContent = act ? (v >= 0 ? '+' : '') + v.toFixed(1) + '%' : '미반응'
        const ttLag = document.getElementById('ttLag')
        if (ttLag) ttLag.textContent = 'lag ' + d.lag + '개월'
        const ttVol = document.getElementById('ttVol')
        if (ttVol) ttVol.textContent = (d.vol >= 0 ? '+' : '') + d.vol + '%'
        const ttFinal = document.getElementById('ttFinal')
        if (ttFinal) ttFinal.textContent = (d.change >= 0 ? '+' : '') + d.change.toFixed(1) + '%'

        const tt = document.getElementById('tooltip')
        if (tt) {
          tt.style.display = 'block'
          let tx = e.originalEvent.clientX + 14
          if (tx + 160 > window.innerWidth) tx = e.originalEvent.clientX - 174
          tt.style.left = tx + 'px'
          tt.style.top  = (e.originalEvent.clientY - 10) + 'px'
        }
      })

      map!.on('mouseleave', 'districts-3d', () => {
        map!.getCanvas().style.cursor = ''
        const tt = document.getElementById('tooltip')
        if (tt) tt.style.display = 'none'
      })

      setProgress(100, '완료')
      mapLoaded = true

      setTimeout(() => {
        const ld = document.getElementById('loading')
        if (ld) {
          ld.style.opacity = '0'
          ld.style.transition = 'opacity .5s'
          setTimeout(() => { ld.style.display = 'none' }, 500)
        }
      }, 300)

      startAnim()
    } catch (err) {
      const ldTxt = document.getElementById('ldTxt')
      if (ldTxt) ldTxt.textContent = '로딩 실패: ' + (err as Error).message
      console.error(err)
    }
  })
})

onUnmounted(() => {
  if (animId !== null) cancelAnimationFrame(animId)
  if (map) { map.remove(); map = null }
})
</script>

<template>
  <div id="map"></div>
  <div class="tt" id="tooltip">
    <div class="tt-nm" id="ttName"></div>
    <div class="tt-r"><span>현재 변화율</span><span class="tt-v" id="ttChange">—</span></div>
    <div class="tt-r"><span>반응 시차</span><span class="tt-v" id="ttLag">—</span></div>
    <div class="tt-r"><span>거래량 변화</span><span class="tt-v" id="ttVol">—</span></div>
    <div class="tt-r"><span>최종 변화율</span><span class="tt-v" id="ttFinal">—</span></div>
  </div>
</template>
