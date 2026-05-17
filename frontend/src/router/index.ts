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
import { useSubscriptionStore } from '@/stores/subscription'
import Layout from '@/components/Layout.vue'
import LandingView from '@/views/LandingView.vue'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import BudgetDetailView from '@/views/BudgetDetailView.vue'
import RecurringView from '@/views/RecurringView.vue'
import HistoryView from '@/views/HistoryView.vue'
import ChartsView from '@/views/ChartsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import AuthCallbackView from '@/views/AuthCallbackView.vue'
import PricingView from '@/views/PricingView.vue'
import SubscriptionSuccessView from '@/views/SubscriptionSuccessView.vue'
import SubscriptionCancelView from '@/views/SubscriptionCancelView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/welcome',
      name: 'welcome',
      component: LandingView,
    },
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
      path: '/pricing',
      name: 'pricing',
      component: PricingView,
    },
    {
      path: '/subscription/success',
      name: 'subscription-success',
      component: SubscriptionSuccessView,
      meta: { requiresAuth: true },
    },
    {
      path: '/subscription/cancel',
      name: 'subscription-cancel',
      component: SubscriptionCancelView,
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
          meta: { requiresPro: true },
        },
        {
          path: 'pro/history',
          name: 'pro-history',
          component: () => import('@/views/pro/ProHistoryView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/charts',
          name: 'pro-charts',
          component: () => import('@/views/pro/ProChartsView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/clients',
          name: 'pro-clients',
          component: () => import('@/views/pro/ProClientsView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/products',
          name: 'pro-products',
          component: () => import('@/views/pro/ProProductsView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/coupons',
          name: 'pro-coupons',
          component: () => import('@/views/pro/ProCouponsView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/gift-cards',
          name: 'pro-gift-cards',
          component: () => import('@/views/pro/ProGiftCardsView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/invoices',
          name: 'pro-invoices',
          component: () => import('@/views/pro/ProInvoicesView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/invoices/new',
          name: 'pro-invoice-new',
          component: () => import('@/views/pro/ProInvoiceDetailView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/invoices/:id',
          name: 'pro-invoice-detail',
          component: () => import('@/views/pro/ProInvoiceDetailView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/quotes',
          name: 'pro-quotes',
          component: () => import('@/views/pro/ProQuotesView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/quotes/new',
          name: 'pro-quote-new',
          component: () => import('@/views/pro/ProQuoteDetailView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/quotes/:id',
          name: 'pro-quote-detail',
          component: () => import('@/views/pro/ProQuoteDetailView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/categories',
          name: 'pro-categories',
          component: () => import('@/views/pro/ProCategoriesView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/declaration',
          name: 'pro-declaration',
          component: () => import('@/views/pro/ProDeclarationView.vue'),
          meta: { requiresPro: true },
        },
        {
          path: 'pro/recurring',
          name: 'pro-recurring',
          component: () => import('@/views/pro/ProRecurringView.vue'),
          meta: { requiresPro: true },
        },
        // Admin routes
        {
          path: 'admin',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/AdminDashboardView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'admin/users',
          name: 'admin-users',
          component: () => import('@/views/admin/AdminUsersView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'admin/quotes',
          name: 'admin-quotes',
          component: () => import('@/views/admin/AdminQuotesView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'admin/invitations',
          name: 'admin-invitations',
          component: () => import('@/views/admin/AdminInvitationsView.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
  ],
})

/**
 * Navigation guard to protect routes requiring authentication.
 * Redirects unauthenticated users to OIDC login for protected routes.
 * Redirects authenticated users to /dashboard if they visit /login.
 * Redirects non-Pro users to /pricing for Pro routes.
 */
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const subscriptionStore = useSubscriptionStore()

  // Allow public routes without authentication
  const publicPaths = ['/auth/success', '/welcome', '/pricing', '/subscription/cancel']
  if (publicPaths.includes(to.path)) {
    next()
    return
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Redirect to landing page for unauthenticated users
    next('/welcome')
    return
  }

  // Check admin access (use matched for nested routes)
  if (to.matched.some(record => record.meta.requiresAdmin) && !authStore.user?.is_admin) {
    next('/dashboard')
    return
  }

  // Check Pro access for Pro routes
  if (to.matched.some(record => record.meta.requiresPro)) {
    // Fetch pro access status if not already loaded
    if (!subscriptionStore.proAccess) {
      await subscriptionStore.fetchProAccess()
    }
    if (!subscriptionStore.hasProAccess) {
      next('/pricing')
      return
    }
  }

  if ((to.path === '/login' || to.path === '/welcome') && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router