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
import ProfileView from '@/views/ProfileView.vue'
import AuthCallbackView from '@/views/AuthCallbackView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/auth/success',
      name: 'auth-callback',
      component: AuthCallbackView,
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
          path: 'loans',
          name: 'loans',
          component: () => import('@/views/LoansView.vue'),
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/ProjectsView.vue'),
        },
        {
          path: 'projects/:id',
          name: 'project-detail',
          component: () => import('@/views/ProjectDetailView.vue'),
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
        },
        {
          path: 'pro',
          name: 'pro-dashboard',
          component: () => import('@/views/pro/ProDashboardView.vue'),
        },
        {
          path: 'pro/history',
          name: 'pro-history',
          component: () => import('@/views/pro/ProHistoryView.vue'),
        },
        {
          path: 'pro/charts',
          name: 'pro-charts',
          component: () => import('@/views/pro/ProChartsView.vue'),
        },
        {
          path: 'pro/clients',
          name: 'pro-clients',
          component: () => import('@/views/pro/ProClientsView.vue'),
        },
        {
          path: 'pro/products',
          name: 'pro-products',
          component: () => import('@/views/pro/ProProductsView.vue'),
        },
        {
          path: 'pro/coupons',
          name: 'pro-coupons',
          component: () => import('@/views/pro/ProCouponsView.vue'),
        },
        {
          path: 'pro/gift-cards',
          name: 'pro-gift-cards',
          component: () => import('@/views/pro/ProGiftCardsView.vue'),
        },
        {
          path: 'pro/invoices',
          name: 'pro-invoices',
          component: () => import('@/views/pro/ProInvoicesView.vue'),
        },
        {
          path: 'pro/invoices/new',
          name: 'pro-invoice-new',
          component: () => import('@/views/pro/ProInvoiceDetailView.vue'),
        },
        {
          path: 'pro/invoices/:id',
          name: 'pro-invoice-detail',
          component: () => import('@/views/pro/ProInvoiceDetailView.vue'),
        },
        {
          path: 'pro/quotes',
          name: 'pro-quotes',
          component: () => import('@/views/pro/ProQuotesView.vue'),
        },
        {
          path: 'pro/quotes/new',
          name: 'pro-quote-new',
          component: () => import('@/views/pro/ProQuoteDetailView.vue'),
        },
        {
          path: 'pro/quotes/:id',
          name: 'pro-quote-detail',
          component: () => import('@/views/pro/ProQuoteDetailView.vue'),
        },
        {
          path: 'pro/categories',
          name: 'pro-categories',
          component: () => import('@/views/pro/ProCategoriesView.vue'),
        },
        {
          path: 'pro/declaration',
          name: 'pro-declaration',
          component: () => import('@/views/pro/ProDeclarationView.vue'),
        },
        {
          path: 'pro/recurring',
          name: 'pro-recurring',
          component: () => import('@/views/pro/ProRecurringView.vue'),
        },
      ],
    },
  ],
})

/**
 * Navigation guard to protect routes requiring authentication.
 * Redirects unauthenticated users to OIDC login for protected routes.
 * Redirects authenticated users to /dashboard if they visit /login.
 */
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Allow auth callback without authentication
  if (to.path === '/auth/success') {
    next()
    return
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // In production, redirect to OIDC login; in dev, use local login page
    if (import.meta.env.PROD) {
      window.location.href = '/auth/login'
    } else {
      next('/login')
    }
    return
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router