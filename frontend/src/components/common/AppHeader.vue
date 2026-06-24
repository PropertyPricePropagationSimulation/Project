<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { computed } from 'vue'

const router    = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

const displayName = computed(() =>
  authStore.isAdmin
    ? `${authStore.nickname} (관리자)`
    : authStore.nickname
)
</script>

<template>
  <header class="ah">
    <div class="ah-inner">
      <router-link to="/" class="ah-logo">
        <span class="ah-logo-sq">EF</span>
        <span class="ah-logo-nm">EstateFlow</span>
      </router-link>

      <nav class="ah-nav">
        <router-link to="/analysis" class="ah-a">분석</router-link>
        <router-link to="/search"   class="ah-a">거래 검색</router-link>
        <router-link to="/notices"  class="ah-a">공지사항</router-link>
        <router-link to="/qna"      class="ah-a">Q&A</router-link>
      </nav>

      <div class="ah-auth">
        <template v-if="authStore.isLoggedIn">
          <router-link to="/mypage" class="ah-nick">
            {{ displayName }}
          </router-link>
          <button class="ah-btn-out" @click="handleLogout">로그아웃</button>
        </template>
        <template v-else>
          <router-link to="/login"    class="ah-btn-login">로그인</router-link>
          <router-link to="/register" class="ah-btn-reg">회원가입</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.ah { position: sticky; top: 0; z-index: 100; background: rgba(255,255,255,.95); backdrop-filter: blur(8px); border-bottom: 1px solid #e2e8f0; }
.ah-inner { max-width: 1100px; margin: 0 auto; padding: 0 24px; height: 60px; display: flex; align-items: center; gap: 32px; }
.ah-logo { display: flex; align-items: center; gap: 8px; text-decoration: none; }
.ah-logo-sq { width: 28px; height: 28px; background: #1e293b; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font: 700 11px 'Inter', sans-serif; }
.ah-logo-nm { font: 600 16px 'Inter', sans-serif; color: #1e293b; }
.ah-nav { display: flex; gap: 4px; margin-left: 16px; flex: 1; }
.ah-a { padding: 6px 12px; border-radius: 6px; text-decoration: none; color: #64748b; font-size: 14px; font-weight: 500; transition: all .15s; }
.ah-a:hover, .ah-a.router-link-active { background: #f1f5f9; color: #1e293b; }
.ah-auth { display: flex; align-items: center; gap: 8px; }
.ah-nick { font-size: 14px; color: #475569; font-weight: 500; text-decoration: none; transition: color .15s; }
.ah-nick:hover { color: #1e293b; }
.ah-btn-login { padding: 7px 14px; border-radius: 6px; text-decoration: none; color: #475569; font-size: 14px; font-weight: 500; border: 1px solid #e2e8f0; transition: all .15s; }
.ah-btn-login:hover { border-color: #cbd5e1; color: #1e293b; }
.ah-btn-reg { padding: 7px 14px; border-radius: 6px; text-decoration: none; background: #1e293b; color: #fff; font-size: 14px; font-weight: 500; transition: background .15s; }
.ah-btn-reg:hover { background: #334155; }
.ah-btn-out { padding: 7px 14px; border-radius: 6px; background: none; border: 1px solid #e2e8f0; color: #64748b; font-size: 14px; cursor: pointer; transition: all .15s; }
.ah-btn-out:hover { border-color: #cbd5e1; color: #1e293b; }
</style>
