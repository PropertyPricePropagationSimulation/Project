const fs = require('fs')
const path = require('path')

const geojsonDir = path.resolve(__dirname, '../public/geojson')
const sourcePath = path.join(geojsonDir, 'sig.json')
const targetPath = path.join(geojsonDir, 'gyeonggi.json')

const koreanNamesByCode = {
  41111: '수원시장안구', 41113: '수원시권선구', 41115: '수원시팔달구', 41117: '수원시영통구',
  41131: '성남시수정구', 41133: '성남시중원구', 41135: '성남시분당구', 41150: '의정부시',
  41171: '안양시만안구', 41173: '안양시동안구', 41192: '부천시원미구', 41194: '부천시소사구',
  41196: '부천시오정구', 41210: '광명시', 41220: '평택시', 41250: '동두천시',
  41271: '안산시상록구', 41273: '안산시단원구', 41281: '고양시덕양구', 41285: '고양시일산동구',
  41287: '고양시일산서구', 41290: '과천시', 41310: '구리시', 41360: '남양주시',
  41370: '오산시', 41390: '시흥시', 41410: '군포시', 41430: '의왕시', 41450: '하남시',
  41461: '용인시처인구', 41463: '용인시기흥구', 41465: '용인시수지구', 41480: '파주시',
  41500: '이천시', 41550: '안성시', 41570: '김포시', 41591: '화성시만세구',
  41593: '화성시효행구', 41595: '화성시병점구', 41597: '화성시동탄구', 41610: '광주시',
  41630: '양주시', 41650: '포천시', 41670: '여주시', 41800: '연천군', 41820: '가평군',
  41830: '양평군',
}

// 현재 수집 완료된 경기도 시·구 코드만 지도에 노출한다.
const targetGyeonggiCodes = new Set([
  '41111', '41113', '41115', '41117', // 수원시
  '41131', '41133', '41135', // 성남시
  '41171', '41173', // 안양시
  '41192', '41194', '41196', // 부천시
  '41271', // 안산시 상록구
  '41290', // 과천시
  '41281', '41285', '41287', // 고양시
  '41410', // 군포시
  '41430', // 의왕시
  '41461', '41463', '41465', // 용인시
  '41570', // 김포시
])

function readJson(filePath) {
  let text = fs.readFileSync(filePath, 'utf8')
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1)
  return JSON.parse(text)
}

// EPSG:5179 (Korea 2000 / Unified CS) -> EPSG:4326 (WGS 84)
function toWgs84([x, y]) {
  const a = 6378137
  const f = 1 / 298.257222101
  const e2 = 2 * f - f * f
  const ePrime2 = e2 / (1 - e2)
  const k0 = 0.9996
  const lon0 = 127.5 * Math.PI / 180
  const lat0 = 38 * Math.PI / 180
  const falseEasting = 1000000
  const falseNorthing = 2000000

  const meridionalArc = latitude => a * (
    (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * latitude
    - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * Math.sin(2 * latitude)
    + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * Math.sin(4 * latitude)
    - (35 * e2 ** 3 / 3072) * Math.sin(6 * latitude)
  )

  const m = meridionalArc(lat0) + (y - falseNorthing) / k0
  const mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
  const e1 = (1 - Math.sqrt(1 - e2)) / (1 + Math.sqrt(1 - e2))
  const phi1 = mu
    + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * Math.sin(2 * mu)
    + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * Math.sin(4 * mu)
    + (151 * e1 ** 3 / 96) * Math.sin(6 * mu)
    + (1097 * e1 ** 4 / 512) * Math.sin(8 * mu)
  const sinPhi1 = Math.sin(phi1)
  const cosPhi1 = Math.cos(phi1)
  const tanPhi1 = Math.tan(phi1)
  const n1 = a / Math.sqrt(1 - e2 * sinPhi1 ** 2)
  const r1 = a * (1 - e2) / (1 - e2 * sinPhi1 ** 2) ** 1.5
  const t1 = tanPhi1 ** 2
  const c1 = ePrime2 * cosPhi1 ** 2
  const d = (x - falseEasting) / (n1 * k0)
  const latitude = phi1 - (n1 * tanPhi1 / r1) * (
    d ** 2 / 2
    - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ePrime2) * d ** 4 / 24
    + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ePrime2 - 3 * c1 ** 2) * d ** 6 / 720
  )
  const longitude = lon0 + (
    d
    - (1 + 2 * t1 + c1) * d ** 3 / 6
    + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ePrime2 + 24 * t1 ** 2) * d ** 5 / 120
  ) / cosPhi1

  return [longitude * 180 / Math.PI, latitude * 180 / Math.PI]
}

function transformCoordinates(coordinates) {
  if (typeof coordinates[0] === 'number') return toWgs84(coordinates)
  return coordinates.map(transformCoordinates)
}

function hasCoordinates(coordinates) {
  if (!Array.isArray(coordinates)) return false
  if (typeof coordinates[0] === 'number') return true
  return coordinates.some(hasCoordinates)
}

const source = readJson(sourcePath)
const features = source.features
  .filter(feature =>
    targetGyeonggiCodes.has(feature.properties.SIG_CD)
    && hasCoordinates(feature.geometry.coordinates),
  )
  .map(feature => ({
    type: 'Feature',
    properties: {
      code: feature.properties.SIG_CD,
      name: koreanNamesByCode[feature.properties.SIG_CD],
      name_eng: feature.properties.SIG_ENG_NM,
      base_year: '2025',
    },
    geometry: {
      type: feature.geometry.type,
      coordinates: transformCoordinates(feature.geometry.coordinates),
    },
  }))

fs.writeFileSync(targetPath, `${JSON.stringify({ type: 'FeatureCollection', features })}\n`, 'utf8')
console.log(`Wrote ${features.length} Gyeonggi-do features to ${targetPath}`)
