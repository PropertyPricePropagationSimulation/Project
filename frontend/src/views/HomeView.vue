<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import { getNotices } from '@/api/noticeApi'

const router  = useRouter()
const notices = ref([])

onMounted(async () => {
  try {
    const res = await getNotices(1, 3)
    notices.value = res.content
  } catch {}
})

function fmtDate(s) { return s?.slice(0, 10) ?? '' }
</script>

<template>
  <div class="home">
    <AppHeader />

    <!-- HERO -->
    <section class="h-hero">
      <div class="h-hero-inner">
        <div class="h-badge">부동산 정책 분석 플랫폼</div>
        <h1 class="h-headline">
          정책 충격이<br>어떻게 번져나가는가
        </h1>
        <p class="h-sub">
          규제·완화 이벤트 기준 서울 아파트 가격 변동을 시각화하고<br>
          지역 간 파급 효과와 시차를 AI로 분석합니다.
        </p>
        <div class="h-cta-row">
          <router-link to="/analysis" class="h-cta-main">분석 시작하기 →</router-link>
          <router-link to="/search"   class="h-cta-sub">거래 검색</router-link>
        </div>
      </div>
      <div class="h-hero-deco" aria-hidden="true">
        <div class="h-map-mock">
          <div class="h-pulse p1"></div>
          <div class="h-pulse p2"></div>
          <div class="h-pulse p3"></div>
        </div>
      </div>
    </section>

    <!-- FEATURES -->
    <section class="h-feat">
      <div class="h-sect-inner">
        <div class="h-feat-card">
          <div class="h-feat-icon">📍</div>
          <h3>이벤트 기반 분석</h3>
          <p>정책 발표일을 기준으로 T-3 ~ T+12개월의 가격 변동 패턴을 추적합니다.</p>
        </div>
        <div class="h-feat-card">
          <div class="h-feat-icon">🌊</div>
          <h3>풍선효과 감지</h3>
          <p>규제 지역에서 인근 지역으로 수요가 이동하는 파급 흐름을 시각화합니다.</p>
        </div>
        <div class="h-feat-card">
          <div class="h-feat-icon">🤖</div>
          <h3>AI 리포트</h3>
          <p>분석 결과를 AI가 요약하고 PDF 리포트로 제공합니다.</p>
        </div>
      </div>
    </section>

    <!-- NOTICES -->
    <section class="h-notices">
      <div class="h-sect-inner">
        <div class="h-sect-hdr">
          <h2>공지사항</h2>
          <router-link to="/notices" class="h-more">전체 보기 →</router-link>
        </div>
        <ul v-if="notices.length" class="h-notice-list">
          <li v-for="n in notices" :key="n.noticeId" class="h-notice-item"
              @click="router.push(`/notices/${n.noticeId}`)">
            <span class="h-notice-title">{{ n.title }}</span>
            <span class="h-notice-date">{{ fmtDate(n.createdAt) }}</span>
          </li>
        </ul>
        <p v-else class="h-notice-empty">등록된 공지사항이 없습니다.</p>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="h-footer">
      <div class="h-sect-inner">
        <span class="h-footer-logo">EstateFlow</span>
        <span class="h-footer-copy">© 2025 EstateFlow. 부동산 정책 충격 전파 분석 시스템.</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.home { min-height: 100vh; background: #f8fafc; color: #1e293b; font-family: 'Noto Sans KR', 'Inter', sans-serif; }

/* HERO */
.h-hero { min-height: 480px; background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); display: flex; align-items: center; padding: 80px 24px; gap: 40px; }
.h-hero-inner { max-width: 560px; margin: 0 auto 0 calc((100% - 1100px)/2 + 24px); }
.h-badge { display: inline-block; padding: 4px 12px; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2); border-radius: 20px; font-size: 12px; color: rgba(255,255,255,.8); margin-bottom: 20px; letter-spacing: .5px; }
.h-headline { font-size: clamp(32px, 5vw, 48px); font-weight: 700; color: #fff; line-height: 1.25; margin-bottom: 16px; }
.h-sub { font-size: 15px; color: rgba(255,255,255,.65); line-height: 1.7; margin-bottom: 32px; }
.h-cta-row { display: flex; gap: 12px; flex-wrap: wrap; }
.h-cta-main { padding: 12px 24px; background: #3b82f6; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; transition: background .15s; }
.h-cta-main:hover { background: #2563eb; }
.h-cta-sub { padding: 12px 24px; background: rgba(255,255,255,.08); color: rgba(255,255,255,.85); border: 1px solid rgba(255,255,255,.2); border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 15px; transition: all .15s; }
.h-cta-sub:hover { background: rgba(255,255,255,.15); }
.h-hero-deco { flex: 1; display: flex; justify-content: center; align-items: center; }
.h-map-mock { width: 240px; height: 240px; position: relative; opacity: .6; }
.h-pulse { position: absolute; border-radius: 50%; animation: pulse 3s ease-in-out infinite; }
.p1 { width: 80px; height: 80px; background: rgba(59,130,246,.4); top: 50%; left: 50%; transform: translate(-50%,-50%); animation-delay: 0s; }
.p2 { width: 140px; height: 140px; border: 2px solid rgba(59,130,246,.3); top: 50%; left: 50%; transform: translate(-50%,-50%); animation-delay: .8s; }
.p3 { width: 210px; height: 210px; border: 1px solid rgba(59,130,246,.15); top: 50%; left: 50%; transform: translate(-50%,-50%); animation-delay: 1.6s; }
@keyframes pulse { 0%,100% { opacity: .3; transform: translate(-50%,-50%) scale(.95); } 50% { opacity: 1; transform: translate(-50%,-50%) scale(1.05); } }

/* FEATURES */
.h-feat { padding: 64px 24px; background: #fff; }
.h-sect-inner { max-width: 1100px; margin: 0 auto; }
.h-feat-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px; }
.h-sect-inner { display: grid; gap: 24px; }
.h-feat .h-sect-inner { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.h-feat-icon { font-size: 28px; margin-bottom: 12px; }
.h-feat-card h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
.h-feat-card p { font-size: 14px; color: #64748b; line-height: 1.6; }

/* NOTICES */
.h-notices { padding: 64px 24px; background: #f8fafc; }
.h-notices .h-sect-inner { display: block; }
.h-sect-hdr { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.h-sect-hdr h2 { font-size: 20px; font-weight: 700; color: #1e293b; }
.h-more { font-size: 13px; color: #3b82f6; text-decoration: none; }
.h-more:hover { text-decoration: underline; }
.h-notice-list { list-style: none; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; background: #fff; }
.h-notice-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background .12s; }
.h-notice-item:last-child { border-bottom: none; }
.h-notice-item:hover { background: #f8fafc; }
.h-notice-title { font-size: 14px; color: #1e293b; font-weight: 500; }
.h-notice-date { font-size: 12px; color: #94a3b8; }
.h-notice-empty { text-align: center; color: #94a3b8; font-size: 14px; padding: 32px 0; }

/* FOOTER */
.h-footer { padding: 24px; background: #1e293b; }
.h-footer .h-sect-inner { display: flex; align-items: center; gap: 16px; }
.h-footer-logo { font-size: 14px; font-weight: 700; color: rgba(255,255,255,.8); }
.h-footer-copy { font-size: 12px; color: rgba(255,255,255,.4); }
</style>
