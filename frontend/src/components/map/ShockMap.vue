<script setup lang="ts">
import { watch, onMounted, onUnmounted, nextTick } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { RegionResult } from '@/types/analysis'
import { LAWD_CD_TO_NAME } from '@/constants/regionCodes'
import { valToColor } from '@/utils/colorScale'

const props = defineProps<{
  regions: RegionResult[]
  currentRelativeMonth: number // -3 ~ +windowMonths
  showLabels: boolean
  paused: boolean
  playing: boolean
}>()

const emit = defineEmits<{
  'region-click': [{ dong_code: string; name: string }]
}>()

const INIT = { center: [127.02, 37.52] as [number, number], zoom: 10.2, pitch: 55, bearing: -10 }
const LERP = 0.12
let map: mapboxgl.Map | null = null
const NODATA = '#d4dae3'
const LINE = 'rgba(20,30,50,.12)'
let baseGeoJSON: Record<string, unknown> | null = null
let mapLoaded = false
let animId: number | null = null
let labelPoints: Array<Record<string, unknown>> = []
const dispVals: Record<string, number> = {}
const regionMap: Record<string, RegionResult> = {}

function polygonCentroid(ring: number[][]): [number, number] {
  let area = 0, cx = 0, cy = 0
  const n = ring.length - 1 // closed ring: last === first
  for (let i = 0; i < n; i++) {
    const x0 = ring[i]![0]!, y0 = ring[i]![1]!
    const x1 = ring[i + 1]![0]!, y1 = ring[i + 1]![1]!
    const cross = x0 * y1 - x1 * y0
    area += cross
    cx   += (x0 + x1) * cross
    cy   += (y0 + y1) * cross
  }
  area /= 2
  return [cx / (6 * area), cy / (6 * area)]
}

function featureCentroid(f: Record<string, unknown>): [number, number] {
  const geom = f.geometry as { type: string; coordinates: unknown }
  if (geom.type === 'Polygon') {
    return polygonCentroid((geom.coordinates as number[][][])[0]!)
  }
  // MultiPolygon: 꼭짓점 수가 가장 많은(= 가장 큰) polygon의 exterior ring 사용
  const polys = geom.coordinates as number[][][][]
  const ring = polys.reduce((max, p) => p[0]!.length > max[0]!.length ? p : max)[0]!
  return polygonCentroid(ring)
}

function buildLabelPoints(features: Array<Record<string, unknown>>) {
  labelPoints = features.map((f) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: featureCentroid(f) },
    properties: {
      name: (f.properties as Record<string, unknown>).name,
      labelColor: '#64748b',
    },
  }))
}

function buildRegionMap() {
  Object.keys(regionMap).forEach((k) => delete regionMap[k])
  props.regions.forEach((r) => {
    const name = LAWD_CD_TO_NAME[r.dong_code]
    if (name) regionMap[name] = r
  })
}

// monthly 실제 데이터에서 해당 상대월의 가격 변화율을 가져옴
function getTarget(name: string): number {
  const region = regionMap[name]
  if (!region) return 0
  const md = region.monthly.find((m) => m.relative_month === props.currentRelativeMonth)
  return md?.price_change_from_event_pct ?? 0
}

function pushMapData() {
  if (!baseGeoJSON || !map) return

  // polygon source: fill-extrusion 색/높이
  const features = (baseGeoJSON.features as Array<Record<string, unknown>>).map((f) => {
    const p = f.properties as Record<string, unknown>
    const name = p.name as string
    const region = regionMap[name]
    const v = dispVals[name] ?? 0
    const lag = region?.window_summary.lag_months ?? null
    const active = lag !== null && props.currentRelativeMonth >= lag ? 1 : 0
    return {
      ...f,
      properties: {
        ...p,
        value: v,
        height: region ? Math.max(20, 300 + Math.sign(v) * Math.max(0, Math.abs(v) - 5) * 60) : 0,
        base: 0,
        fillColor: region ? valToColor(v) : NODATA,
        active,
      },
    }
  })
  const src = map.getSource('districts') as mapboxgl.GeoJSONSource | undefined
  if (src)
    src.setData({ type: 'FeatureCollection', features } as unknown as Parameters<typeof src.setData>[0])

  // label point source: labelColor만 갱신
  const labelFeatures = labelPoints.map((f) => {
    const name = (f.properties as Record<string, unknown>).name as string
    const v = dispVals[name] ?? 0
    return {
      ...f,
      properties: {
        ...(f.properties as object),
        labelColor: regionMap[name] && Math.abs(v) > 2 ? valToColor(v) : '#64748b',
      },
    }
  })
  const labelSrc = map.getSource('district-label-points') as mapboxgl.GeoJSONSource | undefined
  if (labelSrc)
    labelSrc.setData({ type: 'FeatureCollection', features: labelFeatures } as unknown as Parameters<typeof labelSrc.setData>[0])
}

// 수동 스크럽: playing=false일 때만 즉시 스냅 (playing=true는 rAF 루프가 처리)
watch(
  () => props.currentRelativeMonth,
  () => {
    if (props.playing) return
    Object.keys(regionMap).forEach((name) => { dispVals[name] = getTarget(name) })
    if (mapLoaded) pushMapData()
  },
)

// 자동 재생: LERP 0.12 → 800ms 인터벌 안에 수렴, play 종료 후 자연스럽게 완료
function startAnim() {
  if (animId !== null) cancelAnimationFrame(animId)
  function loop() {
    let moved = false
    Object.keys(regionMap).forEach((name) => {
      const target = getTarget(name)
      const cur = dispVals[name] ?? 0
      if (cur === target) return
      const diff = target - cur
      dispVals[name] = Math.abs(diff) > 0.005 ? cur + diff * LERP : target
      moved = true
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

// 서울 25구 전체 로드 — regions가 없어도 지도 구조는 유지
async function loadGeoJSON(): Promise<Record<string, unknown>> {
  setProgress(20, '서울 행정구역 로딩...')
  const geojsons = await Promise.all(
    ['/geojson/seoul.json', '/geojson/gyeonggi.json'].map(
      async (url) => (await (await fetch(url)).json()) as Record<string, unknown>,
    ),
  )
  const seoul = geojsons[0]!
  const gyeonggi = geojsons[1]!
  setProgress(90, '지도 레이어 생성...')
  return {
    type: 'FeatureCollection',
    features: [
      ...(seoul.features as Array<Record<string, unknown>>),
      ...(gyeonggi.features as Array<Record<string, unknown>>),
    ],
  }
}

// 라벨 visibility
watch(
  () => props.showLabels,
  (val) => {
    if (mapLoaded && map) {
      map.setLayoutProperty('districts-labels', 'visibility', val ? 'visible' : 'none')
    }
  },
)

// regions 교체 시 → regionMap 재구성 후 현재 슬라이더 위치로 즉시 스냅
watch(
  () => props.regions,
  () => {
    buildRegionMap() // getTarget이 regionMap을 참조하므로 먼저 호출
    Object.keys(dispVals).forEach((k) => {
      dispVals[k] = getTarget(k) // 현재 월 target으로 스냅 (없으면 0)
    })
    if (mapLoaded) pushMapData()
  },
)

// 모달 등 외부에서 paused=true → LERP 즉시 스냅
watch(
  () => props.paused,
  (paused) => {
    if (!paused) return
    Object.keys(regionMap).forEach((name) => {
      dispVals[name] = getTarget(name)
    })
    if (mapLoaded) pushMapData()
  },
)

onMounted(() => {
  buildRegionMap()

  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v11',
    center: [127.02, 37.52],
    zoom: 10.2,
    pitch: 55,
    bearing: -10,
    antialias: true,
  })

map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), 'bottom-right')

  // compass 버튼: bearing만 리셋 → 초기 위치·줌·pitch·bearing 전체 복원으로 교체
  nextTick(() => {
    const compass = map!.getContainer().querySelector('.mapboxgl-ctrl-compass')
    compass?.addEventListener(
      'click',
      (e) => {
        e.stopImmediatePropagation()
        map!.flyTo({ ...INIT, duration: 900, essential: true })
      },
      true,
    )
  })

  map.on('load', async () => {
    map!.getStyle().layers.forEach((layer) => {
      if (layer.type !== 'symbol' || !layer.layout?.['text-field']) return
      // 구/동 이름 레이어는 숨김 — 우리 districts-labels가 대체
      if (/place|settlement|suburb|neighborhood/.test(layer.id)) {
        map!.setLayoutProperty(layer.id, 'visibility', 'none')
      } else {
        map!.setLayoutProperty(layer.id, 'text-field', [
          'coalesce',
          ['get', 'name_ko'],
          ['get', 'name'],
        ])
      }
    })
    try {
      baseGeoJSON = await loadGeoJSON()

      const feats = baseGeoJSON.features as Array<Record<string, unknown>>
      buildLabelPoints(feats)

      baseGeoJSON.features = feats.map((f) => ({
        ...f,
        properties: {
          ...(f.properties as object),
          value: 0,
          height: 0,
          base: 0,
          fillColor: NODATA,
          active: 0,
        },
      }))

      map!.addSource('districts', {
        type: 'geojson',
        data: baseGeoJSON as unknown as mapboxgl.GeoJSONSourceSpecification['data'],
      })

      map!.addSource('district-label-points', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: labelPoints,
        } as unknown as mapboxgl.GeoJSONSourceSpecification['data'],
      })

      map!.addLayer({
        id: 'districts-3d',
        type: 'fill-extrusion',
        source: 'districts',
        paint: {
          'fill-extrusion-color': ['get', 'fillColor'],
          'fill-extrusion-height': ['get', 'height'],
          'fill-extrusion-base': ['get', 'base'],
          'fill-extrusion-opacity': 0.82,
        },
      })

      map!.addLayer({
        id: 'districts-line',
        type: 'line',
        source: 'districts',
        paint: { 'line-color': LINE, 'line-width': 0.7 },
      })

      map!.addLayer({
        id: 'districts-labels',
        type: 'symbol',
        source: 'district-label-points',
        layout: {
          'text-field': ['get', 'name'],
          'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
          'text-size': ['interpolate', ['linear'], ['zoom'], 9, 11, 11, 14, 13, 18],
          'text-offset': [0, 0],
          'text-anchor': 'center',
          'text-allow-overlap': false,
          'text-padding': 6,
          'symbol-avoid-edges': true,
        },
        paint: {
          'text-color': ['get', 'labelColor'],
          'text-halo-color': 'rgba(255,255,255,0.9)',
          'text-halo-width': 2,
        },
      })

      // hover 툴팁 — DOM 직접 조작 (Mapbox 이벤트는 Vue 반응형 밖에서 실행)
      map!.on('mousemove', 'districts-3d', (e) => {
        map!.getCanvas().style.cursor = 'pointer'
        const feature = e.features?.[0] as unknown as
          | { properties: Record<string, unknown> }
          | undefined
        if (!feature) return
        const name = feature.properties.name as string
        const region = regionMap[name]
        if (!region) return

        const v = dispVals[name] ?? 0
        const ws = region.window_summary
        const lag = ws.lag_months
        const active = lag !== null && props.currentRelativeMonth >= lag
        const col = valToColor(ws.final_price_change_pct)

        const ttName = document.getElementById('ttName')
        if (ttName) {
          ttName.textContent = name
          ttName.style.color = col
        }

        const ttChange = document.getElementById('ttChange')
        if (ttChange)
          ttChange.textContent = active ? (v >= 0 ? '+' : '') + v.toFixed(1) + '%' : '미반응'

        const ttLag = document.getElementById('ttLag')
        if (ttLag) ttLag.textContent = lag !== null ? `lag ${lag}개월` : '—'

        const ttVol = document.getElementById('ttVol')
        if (ttVol)
          ttVol.textContent =
            (ws.final_volume_change_pct >= 0 ? '+' : '') +
            ws.final_volume_change_pct.toFixed(1) +
            '%'

        const ttFinal = document.getElementById('ttFinal')
        if (ttFinal)
          ttFinal.textContent =
            (ws.final_price_change_pct >= 0 ? '+' : '') + ws.final_price_change_pct.toFixed(1) + '%'

        const tt = document.getElementById('tooltip')
        if (tt) {
          tt.style.display = 'block'
          let tx = e.originalEvent.clientX + 14
          if (tx + 160 > window.innerWidth) tx = e.originalEvent.clientX - 174
          tt.style.left = tx + 'px'
          tt.style.top = e.originalEvent.clientY - 10 + 'px'
        }
      })

      map!.on('mouseleave', 'districts-3d', () => {
        map!.getCanvas().style.cursor = ''
        const tt = document.getElementById('tooltip')
        if (tt) tt.style.display = 'none'
      })

      map!.on('click', 'districts-3d', (e) => {
        const feature = e.features?.[0] as unknown as
          | { properties: Record<string, unknown> }
          | undefined
        if (!feature) return
        const name = feature.properties.name as string
        const region = regionMap[name]
        if (!region) return
        emit('region-click', { dong_code: region.dong_code, name })
      })

      setProgress(100, '완료')
      mapLoaded = true
      pushMapData()

      setTimeout(() => {
        const ld = document.getElementById('loading')
        if (ld) {
          ld.style.opacity = '0'
          ld.style.transition = 'opacity .5s'
          setTimeout(() => {
            ld.style.display = 'none'
          }, 500)
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
  if (map) {
    map.remove()
    map = null
  }
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
