import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import HomeView         from '@/views/HomeView.vue'
import AnalysisView     from '@/views/AnalysisView.vue'
import SearchView       from '@/views/SearchView.vue'
import NoticeListView   from '@/views/NoticeListView.vue'
import NoticeDetailView from '@/views/NoticeDetailView.vue'
import NoticeWriteView  from '@/views/NoticeWriteView.vue'
import QnaListView      from '@/views/QnaListView.vue'
import QnaDetailView    from '@/views/QnaDetailView.vue'
import QnaWriteView     from '@/views/QnaWriteView.vue'
import LoginView        from '@/views/LoginView.vue'
import RegisterView     from '@/views/RegisterView.vue'
import MyPageView       from '@/views/MyPageView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/',              name: 'home',          component: HomeView },
    { path: '/analysis',      name: 'analysis',      component: AnalysisView },
    { path: '/search',        name: 'search',        component: SearchView },
    { path: '/notices',        name: 'noticeList',   component: NoticeListView },
    { path: '/notices/write',  name: 'noticeWrite',  component: NoticeWriteView, meta: { requiresAuth: true } },
    { path: '/notices/:id',    name: 'noticeDetail', component: NoticeDetailView },
    { path: '/qna',           name: 'qnaList',       component: QnaListView },
    { path: '/qna/write',     name: 'qnaWrite',      component: QnaWriteView, meta: { requiresAuth: true } },
    { path: '/qna/:id',       name: 'qnaDetail',     component: QnaDetailView },
    { path: '/login',         name: 'login',         component: LoginView },
    { path: '/register',      name: 'register',      component: RegisterView },
    { path: '/mypage',        name: 'mypage',        component: MyPageView,  meta: { requiresAuth: true } },
  ],
})

router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth) {
    const auth = useAuthStore()
    if (!auth.isLoggedIn) return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  next()
})

export default router
