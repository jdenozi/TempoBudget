/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Vue Router Configuration
 *
 * Defines all application routes and navigation guards.
 * Protected routes require authentication via the auth store.
 *
 * Route Structure:
 * - /login - Public login page
 * - / (Layout) - Protected routes container
 *   - /dashboard - Main budget overview
 *   - /budget/:id - Individual budget details
 *   - /recurring - Recurring transactions management
 *   - /history - Transaction history
 *   - /charts - Data visualizations
 *   - /profile - User profile settings
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Layout from '@/components/Layout.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import BudgetDetailView from '@/views/BudgetDetailView.vue'
import RecurringView from '@/views/RecurringView.vue'
import HistoryView from '@/views/HistoryView.vue'
import ChartsView from '@/views/ChartsView.vue'
import eView from '@/views/ProfileView.vue'
import ProfileView from '@/views/ProfileView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      component: Layout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'budget/:id',
          name: 'budget-detail',
          component: BudgetDetailView,
        },
        {
          path: 'recurring',
          name: 'recurring',
          component: RecurringView,
        },
        {
          path: 'history',
          name: 'history',
          component: HistoryView,
        },
        {
          path: 'charts',
          name: 'charts',
          component: ChartsView,
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
        },
      ],
    },
  ],
})

/**
 * Navigation guard to protect routes requiring authentication.
 * Redirects unauthenticated users to /login for protected routes.
 * Redirects authenticated users to /dashboard if they visit /login.
 */
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router