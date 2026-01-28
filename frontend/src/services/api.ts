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
   * Retrieves all recurring transactions for a budget.
   * @param budgetId - The budget's unique identifier
   * @returns Array of recurring transactions
   */
  getByBudget: async (budgetId: string) => {
    const response = await api.get<RecurringTransaction[]>(`/budgets/${budgetId}/recurring`)
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
    const response = await api.post<RecurringTransaction>(`/budgets/${data.budget_id}/recurring`, data)
    return response.data
  },

  /**
   * Toggles the active status of a recurring transaction.
   * @param id - Recurring transaction unique identifier
   * @returns The updated recurring transaction
   */
  toggle: async (id: string) => {
    const response = await api.put<RecurringTransaction>(`/recurring/${id}/toggle`, {})
    return response.data
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


export default api