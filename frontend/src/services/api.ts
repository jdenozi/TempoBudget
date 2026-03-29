/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * API Service Module
 *
 * Provides HTTP client configuration and API methods for communicating
 * with the Tempo Budget backend. Includes automatic JWT token injection
 * for authenticated requests.
 *
 * API Groups:
 * - authAPI: User registration and login
 * - budgetsAPI: Budget CRUD operations
 * - categoriesAPI: Budget category management
 * - transactionsAPI: Transaction management
 * - recurringAPI: Recurring transaction templates
 * - budgetMembersAPI: Group budget membership
 * - invitationsAPI: Budget invitation handling
 */

import axios from 'axios'

/** Base URL for the API server */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

/**
 * Configured Axios instance with default headers.
 * JWT token is automatically added via request interceptor.
 */
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor to add JWT token to all requests.
 * Retrieves token from localStorage and adds it to Authorization header.
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Sets up API response interceptors for handling auth errors.
 * Called from main.ts after stores are initialized.
 * @param authStore - The auth store instance
 * @param router - The router instance
 */
export function setupApiInterceptors(
  authStore: { logout: () => void; isAuthenticated: boolean },
  router: { push: (path: string) => void }
) {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle 401 Unauthorized errors (expired/invalid token)
      if (error.response?.status === 401 && authStore.isAuthenticated) {
        // Don't logout for login/register endpoints
        const url = error.config?.url || ''
        if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
          authStore.logout()
          router.push('/login?reason=expired')
        }
      }
      return Promise.reject(error)
    }
  )
}

// ============================================================================
// Type Definitions
// ============================================================================

/** User account information */
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  phone?: string
  created_at: string
  updated_at: string
}

/** Authentication response containing JWT token and user data */
export interface AuthResponse {
  token: string
  user: User
}

/** Budget entity representing a personal or group budget */
export interface Budget {
  id: string
  user_id: string
  name: string
  budget_type: string
  is_active: number
  created_at: string
  updated_at: string
}

/** Budget category for organizing transactions */
export interface Category {
  id: string
  budget_id: string
  parent_id: string | null
  name: string
  amount: number
  tags: string[]
  created_at: string
}

/** Financial transaction (income or expense) */
export interface Transaction {
  id: string
  budget_id: string
  category_id: string
  title: string
  amount: number
  transaction_type: string
  date: string
  comment?: string
  is_recurring: number
  is_budgeted: number
  paid_by_user_id?: string
  created_at: string
}

/** Recurring transaction template */
export interface RecurringTransaction {
  id: string
  budget_id: string
  category_id: string
  title: string
  amount: number
  transaction_type: string
  frequency: string
  day?: number
  active: number
  created_at: string
}

/** Version history entry for recurring transactions */
export interface RecurringTransactionVersion {
  id: string
  recurring_transaction_id: string
  title: string
  amount: number
  category_id: string
  frequency: string
  day?: number
  effective_from: string
  effective_until?: string
  created_at: string
  change_reason?: string
}

/** Recurring transaction with category info */
export interface RecurringTransactionWithCategory extends RecurringTransaction {
  category_name: string
  parent_category_id?: string
  parent_category_name?: string
  pending_version?: RecurringTransactionVersion
}

/** Update payload for recurring transactions */
export interface UpdateRecurringTransactionPayload {
  title?: string
  amount?: number
  category_id?: string
  frequency?: string
  day?: number
  effective_date?: string
  change_reason?: string
}

/** Budget member with associated user information */
export interface BudgetMemberWithUser {
  id: string
  budget_id: string
  user_id: string
  role: string
  share: number
  created_at: string
  user_name: string
  user_email: string
  user_avatar?: string
}

/** Member balance for group budget calculations */
export interface MemberBalance {
  user_id: string
  user_name: string
  share: number
  total_due: number
  total_paid: number
  balance: number
}

/** Budget summary statistics */
export interface BudgetSummary {
  id: string
  name: string
  budget_type: string
  total_budget: number
  income_budget: number
  total_spent: number
  total_income: number
  remaining: number
  percentage: number
  category_count: number
  transaction_count: number
  balance: number
}

/** Budget invitation with full context details */
export interface BudgetInvitationWithDetails {
  id: string
  budget_id: string
  budget_name: string
  inviter_id: string
  inviter_name: string
  invitee_email: string
  role: string
  status: string
  created_at: string
}

// ============================================================================
// API Methods
// ============================================================================

/**
 * Authentication API methods.
 */
export const authAPI = {
  /**
   * Gets current user info from token.
   * @returns User data
   */
  getMe: async () => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  /**
   * Registers a new user account.
   * @param email - User's email address
   * @param name - User's display name
   * @param password - User's password (will be hashed server-side)
   * @returns Authentication response with token and user data
   */
  register: async (email: string, name: string, password: string) => {
    const response = await api.post<AuthResponse>('/auth/register', {
      email,
      name,
      password,
    })
    return response.data
  },

  /**
   * Authenticates an existing user.
   * @param email - User's email address
   * @param password - User's password
   * @returns Authentication response with token and user data
   */
  login: async (email: string, password: string) => {
    const response = await api.post<AuthResponse>('/auth/login', {
      email,
      password,
    })
    return response.data
  },

  /**
   * Changes the current user's password.
   * @param currentPassword - Current password
   * @param newPassword - New password
   */
  changePassword: async (currentPassword: string, newPassword: string) => {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },

  updateProfile: async (data: { name?: string; phone?: string }) => {
    const response = await api.put<User>('/auth/profile', data)
    return response.data
  },

  uploadAvatar: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<User>('/auth/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}

/**
 * Category management API methods.
 */
export const categoriesAPI = {
  /**
   * Retrieves all categories for a budget.
   * @param budgetId - The budget's unique identifier
   * @returns Array of categories
   */
  getByBudget: async (budgetId: string) => {
    const response = await api.get<Category[]>(`/budgets/${budgetId}/categories`)
    return response.data
  },

  /**
   * Creates a new category within a budget.
   * @param budgetId - The budget's unique identifier
   * @param name - Category name
   * @param amount - Allocated amount
   * @returns The created category
   */
  create: async (budgetId: string, name: string, amount: number, parentId?: string, tags?: string[]) => {
    const response = await api.post<Category>(`/budgets/${budgetId}/categories`, {
      name,
      amount,
      parent_id: parentId || null,
      tags: tags || [],
    })
    return response.data
  },

  /**
   * Updates an existing category.
   * @param id - Category unique identifier
   * @param data - Fields to update (name and/or amount)
   * @returns The updated category
   */
  update: async (id: string, data: { name?: string; amount?: number; tags?: string[] }) => {
    const response = await api.put<Category>(`/categories/${id}`, data)
    return response.data
  },

  /**
   * Deletes a category.
   * @param id - Category unique identifier
   */
  delete: async (id: string) => {
    await api.delete(`/categories/${id}`)
  },
}

/**
 * Transaction management API methods.
 */
export const transactionsAPI = {
  /**
   * Retrieves all transactions for a budget.
   * @param budgetId - The budget's unique identifier
   * @returns Array of transactions sorted by date descending
   */
  getByBudget: async (budgetId: string) => {
    const response = await api.get<Transaction[]>(`/budgets/${budgetId}/transactions`)
    return response.data
  },

  /**
   * Creates a new transaction.
   * @param data - Transaction data including budget_id, category_id, title, amount, etc.
   * @returns The created transaction
   */
  create: async (data: {
    budget_id: string
    category_id: string
    title: string
    amount: number
    transaction_type: string
    date: string
    comment?: string
    is_budgeted?: number
    paid_by_user_id?: string
  }) => {
    const response = await api.post<Transaction>(`/budgets/${data.budget_id}/transactions`, data)
    return response.data
  },

  /**
   * Updates an existing transaction.
   * @param id - Transaction unique identifier
   * @param data - Fields to update
   * @returns The updated transaction
   */
  update: async (id: string, data: {
    category_id?: string
    title?: string
    amount?: number
    transaction_type?: string
    date?: string
    comment?: string
    is_budgeted?: number
    paid_by_user_id?: string
  }) => {
    const response = await api.put<Transaction>(`/transactions/${id}`, data)
    return response.data
  },

  /**
   * Deletes a transaction.
   * @param id - Transaction unique identifier
   */
  delete: async (id: string) => {
    await api.delete(`/transactions/${id}`)
  },
}

/**
 * Recurring transaction management API methods.
 */
export const recurringAPI = {
  /**
   * Retrieves all recurring transactions for a budget with category info.
   * @param budgetId - The budget's unique identifier
   * @returns Array of recurring transactions with category info
   */
  getByBudget: async (budgetId: string) => {
    const response = await api.get<RecurringTransactionWithCategory[]>(`/budgets/${budgetId}/recurring`)
    return response.data
  },

  /**
   * Creates a new recurring transaction template.
   * @param data - Recurring transaction data
   * @returns The created recurring transaction
   */
  create: async (data: {
    budget_id: string
    category_id: string
    title: string
    amount: number
    transaction_type: string
    frequency: string
    day?: number
  }) => {
    const response = await api.post<RecurringTransactionWithCategory>(`/budgets/${data.budget_id}/recurring`, data)
    return response.data
  },

  /**
   * Toggles the active status of a recurring transaction.
   * @param id - Recurring transaction unique identifier
   * @returns The updated recurring transaction
   */
  toggle: async (id: string) => {
    const response = await api.put<RecurringTransactionWithCategory>(`/recurring/${id}/toggle`, {})
    return response.data
  },

  /**
   * Updates a recurring transaction with optional effective date.
   * @param id - Recurring transaction ID
   * @param data - Fields to update
   * @returns The updated recurring transaction
   */
  update: async (id: string, data: UpdateRecurringTransactionPayload) => {
    const response = await api.put<RecurringTransactionWithCategory>(`/recurring/${id}`, data)
    return response.data
  },

  /**
   * Retrieves version history for a recurring transaction.
   * @param id - Recurring transaction ID
   * @returns Array of version records
   */
  getVersions: async (id: string) => {
    const response = await api.get<RecurringTransactionVersion[]>(`/recurring/${id}/versions`)
    return response.data
  },

  /**
   * Cancels a scheduled (future) version.
   * @param versionId - Version ID to cancel
   */
  cancelVersion: async (versionId: string) => {
    await api.delete(`/recurring/versions/${versionId}`)
  },

  /**
   * Deletes a recurring transaction.
   * @param id - Recurring transaction unique identifier
   */
  delete: async (id: string) => {
    await api.delete(`/recurring/${id}`)
  },

  /**
   * Process recurring transactions and generate actual transactions.
   * Creates transactions for any recurring templates that should have triggered.
   * @param budgetId - The budget's unique identifier
   * @returns Array of newly created transactions
   */
  process: async (budgetId: string) => {
    const response = await api.post<Transaction[]>(`/budgets/${budgetId}/recurring/process`)
    return response.data
  },
}

/**
 * Budget member management API methods for group budgets.
 */
export const budgetMembersAPI = {
  /**
   * Retrieves all members of a budget.
   * @param budgetId - The budget's unique identifier
   * @returns Array of budget members with user information
   */
  getMembers: async (budgetId: string) => {
    const response = await api.get<BudgetMemberWithUser[]>(`/budgets/${budgetId}/members`)
    return response.data
  },

  /**
   * Invites a user to join a budget.
   * @param budgetId - The budget's unique identifier
   * @param email - Email address of the user to invite
   * @param role - Role to assign (default: 'member')
   */
  inviteMember: async (budgetId: string, email: string, role: string = 'member') => {
    await api.post(`/budgets/${budgetId}/members`, {
      email,
      role,
    })
  },

  /**
   * Removes a member from a budget.
   * @param budgetId - The budget's unique identifier
   * @param memberId - The member record's unique identifier
   */
  removeMember: async (budgetId: string, memberId: string) => {
    await api.delete(`/budgets/${budgetId}/members/${memberId}`)
  },

  /**
   * Updates a member's share percentage.
   * @param budgetId - The budget's unique identifier
   * @param memberId - The member record's unique identifier
   * @param share - New share percentage (0-100)
   */
  updateShare: async (budgetId: string, memberId: string, share: number) => {
    const response = await api.put<BudgetMemberWithUser>(
      `/budgets/${budgetId}/members/${memberId}/share`,
      { share }
    )
    return response.data
  },

  /**
   * Gets the balance calculations for all members.
   * @param budgetId - The budget's unique identifier
   * @returns Array of member balances
   */
  getBalances: async (budgetId: string) => {
    const response = await api.get<MemberBalance[]>(`/budgets/${budgetId}/balances`)
    return response.data
  },
}

/**
 * Budget invitation management API methods.
 */
export const invitationsAPI = {
  /**
   * Retrieves all pending invitations for the current user.
   * @returns Array of invitation details
   */
  getMyInvitations: async () => {
    const response = await api.get<BudgetInvitationWithDetails[]>('/invitations')
    return response.data
  },

  /**
   * Accepts a budget invitation.
   * @param id - Invitation unique identifier
   */
  acceptInvitation: async (id: string) => {
    await api.post(`/invitations/${id}/accept`)
  },

  /**
   * Rejects a budget invitation.
   * @param id - Invitation unique identifier
   */
  rejectInvitation: async (id: string) => {
    await api.post(`/invitations/${id}/reject`)
  },
}

/**
 * Budget management API methods.
 */
export const budgetsAPI = {
  /**
   * Retrieves all budgets for the current user.
   * @returns Array of budgets
   */
  getAll: async () => {
    const response = await api.get<Budget[]>('/budgets')
    return response.data
  },

  /**
   * Retrieves summary statistics for all user budgets.
   * @returns Array of budget summaries
   */
  getSummaries: async () => {
    const response = await api.get<BudgetSummary[]>('/budgets/summaries')
    return response.data
  },

  /**
   * Retrieves a specific budget by ID.
   * @param id - Budget unique identifier
   * @returns The budget
   */
  getById: async (id: string) => {
    const response = await api.get<Budget>(`/budgets/${id}`)
    return response.data
  },

  /**
   * Creates a new budget.
   * @param name - Budget name
   * @param budget_type - Either 'personal' or 'group'
   * @returns The created budget
   */
  create: async (name: string, budget_type: string) => {
    const response = await api.post<Budget>('/budgets', {
      name,
      budget_type,
    })
    return response.data
  },

  /**
   * Deletes a budget.
   * @param id - Budget unique identifier
   */
  delete: async (id: string) => {
    await api.delete(`/budgets/${id}`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: null
    })
  },
}


// ============================================================================
// Pro (Auto-Entrepreneur) Types
// ============================================================================

export interface ProProfile {
  id: string
  user_id: string
  siret: string | null
  activity_type: string
  cotisation_rate: number
  declaration_frequency: string
  revenue_threshold: number
  created_at: string
  updated_at: string
}

export interface ProClient {
  id: string
  user_id: string
  name: string
  email: string | null
  phone: string | null
  address: string | null
  notes: string | null
  created_at: string
}

export interface ProCategory {
  id: string
  user_id: string
  name: string
  type: 'income' | 'expense'
  is_default: number
  created_at: string
}

export interface ProProduct {
  id: string
  user_id: string
  name: string
  type: 'product' | 'service' | 'gift_card'
  default_price: number
  category_id: string | null
  created_at: string
  category_name: string | null
}

export interface ProTransactionItem {
  id: string
  transaction_id: string
  product_id: string
  quantity: number
  unit_price: number
  created_at: string
  product_name: string | null
}

export interface ProTransaction {
  id: string
  user_id: string
  client_id: string | null
  category_id: string
  title: string
  amount: number
  transaction_type: 'income' | 'expense'
  date: string
  payment_method: string | null
  comment: string | null
  discount_type: string | null
  discount_value: number | null
  coupon_id: string | null
  gift_card_payment: number
  created_at: string
  client_name: string | null
  category_name: string | null
  items: ProTransactionItem[]
}

export interface ProCoupon {
  id: string
  user_id: string
  code: string
  name: string
  discount_type: 'percentage' | 'fixed'
  discount_value: number
  valid_from: string | null
  valid_until: string | null
  max_uses: number
  used_count: number
  is_active: number
  created_at: string
}

export interface ProGiftCard {
  id: string
  user_id: string
  code: string
  initial_amount: number
  remaining_balance: number
  client_id: string | null
  purchase_transaction_id: string | null
  purchase_date: string
  is_active: number
  created_at: string
  client_name: string | null
}

export interface ProGiftCardUsage {
  id: string
  gift_card_id: string
  transaction_id: string
  amount_used: number
  created_at: string
  transaction_title: string | null
}

export interface ProDashboardSummary {
  ca_month: number
  ca_quarter: number
  ca_year: number
  expenses_month: number
  expenses_quarter: number
  expenses_year: number
  net_month: number
  cotisations_estimated: number
  threshold_percentage: number
}

// ============================================================================
// Pro API Methods
// ============================================================================

export const proProfileAPI = {
  get: async () => {
    const response = await api.get<ProProfile>('/pro/profile')
    return response.data
  },
  update: async (data: Partial<ProProfile>) => {
    const response = await api.put<ProProfile>('/pro/profile', data)
    return response.data
  },
}

export const proClientsAPI = {
  getAll: async () => {
    const response = await api.get<ProClient[]>('/pro/clients')
    return response.data
  },
  create: async (data: { name: string; email?: string; phone?: string; address?: string; notes?: string }) => {
    const response = await api.post<ProClient>('/pro/clients', data)
    return response.data
  },
  update: async (id: string, data: { name?: string; email?: string; phone?: string; address?: string; notes?: string }) => {
    const response = await api.put<ProClient>(`/pro/clients/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/clients/${id}`)
  },
}

export const proCategoriesAPI = {
  getAll: async () => {
    const response = await api.get<ProCategory[]>('/pro/categories')
    return response.data
  },
  create: async (data: { name: string; type: 'income' | 'expense' }) => {
    const response = await api.post<ProCategory>('/pro/categories', data)
    return response.data
  },
  update: async (id: string, data: { name?: string; type?: 'income' | 'expense' }) => {
    const response = await api.put<ProCategory>(`/pro/categories/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/categories/${id}`)
  },
}

export const proProductsAPI = {
  getAll: async () => {
    const response = await api.get<ProProduct[]>('/pro/products')
    return response.data
  },
  create: async (data: { name: string; type: 'product' | 'service' | 'gift_card'; default_price: number; category_id?: string }) => {
    const response = await api.post<ProProduct>('/pro/products', data)
    return response.data
  },
  update: async (id: string, data: { name?: string; type?: 'product' | 'service' | 'gift_card'; default_price?: number; category_id?: string }) => {
    const response = await api.put<ProProduct>(`/pro/products/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/products/${id}`)
  },
}

export const proTransactionsAPI = {
  getAll: async (params?: { start_date?: string; end_date?: string; client_id?: string; category_id?: string; payment_method?: string; product_id?: string }) => {
    const response = await api.get<ProTransaction[]>('/pro/transactions', { params })
    return response.data
  },
  create: async (data: {
    client_id?: string
    category_id: string
    title?: string
    amount?: number
    transaction_type: 'income' | 'expense'
    date: string
    payment_method?: string
    comment?: string
    items?: { product_id: string; quantity: number; unit_price: number }[]
    discount_type?: 'percentage' | 'fixed'
    discount_value?: number
    coupon_id?: string
    gift_card_id?: string
    gift_card_amount?: number
  }) => {
    const response = await api.post<ProTransaction>('/pro/transactions', data)
    return response.data
  },
  update: async (id: string, data: {
    client_id?: string
    category_id?: string
    title?: string
    amount?: number
    transaction_type?: 'income' | 'expense'
    date?: string
    payment_method?: string
    comment?: string
  }) => {
    const response = await api.put<ProTransaction>(`/pro/transactions/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/transactions/${id}`)
  },
}

export const proCouponsAPI = {
  getAll: async () => {
    const response = await api.get<ProCoupon[]>('/pro/coupons')
    return response.data
  },
  create: async (data: {
    code: string; name: string; discount_type: 'percentage' | 'fixed';
    discount_value: number; valid_from?: string; valid_until?: string; max_uses?: number
  }) => {
    const response = await api.post<ProCoupon>('/pro/coupons', data)
    return response.data
  },
  update: async (id: string, data: {
    code?: string; name?: string; discount_type?: 'percentage' | 'fixed';
    discount_value?: number; valid_from?: string; valid_until?: string;
    max_uses?: number; is_active?: number
  }) => {
    const response = await api.put<ProCoupon>(`/pro/coupons/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/coupons/${id}`)
  },
}

export const proGiftCardsAPI = {
  getAll: async () => {
    const response = await api.get<ProGiftCard[]>('/pro/gift-cards')
    return response.data
  },
  getById: async (id: string) => {
    const response = await api.get<ProGiftCard>(`/pro/gift-cards/${id}`)
    return response.data
  },
  create: async (data: { code: string; initial_amount: number; client_id?: string; purchase_date: string }) => {
    const response = await api.post<ProGiftCard>('/pro/gift-cards', data)
    return response.data
  },
  getUsages: async (id: string) => {
    const response = await api.get<ProGiftCardUsage[]>(`/pro/gift-cards/${id}/usages`)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/gift-cards/${id}`)
  },
}

export const proDashboardAPI = {
  getSummary: async () => {
    const response = await api.get<ProDashboardSummary>('/pro/dashboard')
    return response.data
  },
}

export default api