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
  is_admin?: boolean
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
  project_category_id?: string | null
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
/** Invitation validation result */
export interface InvitationValidation {
  valid: boolean
  email: string | null
  expired: boolean
  already_used: boolean
}

/** Invitation for registration */
export interface Invitation {
  id: string
  email: string
  token: string
  invited_by_user_id: string
  created_at: string
  expires_at: string
  used_at: string | null
  used_by_user_id: string | null
}

/** Pro access status */
export interface ProAccessStatus {
  has_pro_access: boolean
  reason: 'subscription' | 'admin_override' | 'none'
}

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
   * Validates an invitation token.
   * @param token - The invitation token from the URL
   * @returns Validation result
   */
  validateInvitation: async (token: string) => {
    const response = await api.get<InvitationValidation>(`/auth/invitation/${token}`)
    return response.data
  },

  /**
   * Registers a new user account (requires invitation).
   * @param email - User's email address
   * @param name - User's display name
   * @param password - User's password (will be hashed server-side)
   * @param invitationToken - Optional invitation token for free trial
   * @returns Authentication response with token and user data
   */
  register: async (email: string, name: string, password: string, invitationToken?: string) => {
    const response = await api.post<AuthResponse>('/auth/register', {
      email,
      name,
      password,
      invitation_token: invitationToken || null,
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
    project_category_id?: string | null
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
    project_category_id?: string | null
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

  exportCSV: async (budgetId: string, params?: { start_date?: string; end_date?: string; category_id?: string }) => {
    const response = await api.get(`/budgets/${budgetId}/transactions/export`, {
      params,
      responseType: 'blob',
    })
    return response.data
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
  getUpcoming: async () => {
    const response = await api.get<UpcomingRecurring[]>('/upcoming-recurring')
    return response.data
  },

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
/**
 * Loans API methods.
 */
export const loansAPI = {
  getAll: async () => {
    const response = await api.get<Loan[]>('/loans')
    return response.data
  },
  getSummary: async () => {
    const response = await api.get<LoanSummary>('/loans/summary')
    return response.data
  },
  create: async (data: { person_name: string; amount: number; direction: 'lent' | 'borrowed'; date: string; description?: string }) => {
    const response = await api.post<Loan>('/loans', data)
    return response.data
  },
  update: async (id: string, data: { person_name?: string; amount?: number; direction?: 'lent' | 'borrowed'; date?: string; description?: string; status?: 'active' | 'repaid' }) => {
    const response = await api.put<Loan>(`/loans/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/loans/${id}`)
  },
  addRepayment: async (loanId: string, data: { amount: number; date: string; comment?: string }) => {
    const response = await api.post<LoanRepayment>(`/loans/${loanId}/repayments`, data)
    return response.data
  },
  deleteRepayment: async (loanId: string, repaymentId: string) => {
    await api.delete(`/loans/${loanId}/repayments/${repaymentId}`)
  },
}

export const projectsAPI = {
  getAll: async (params?: { status?: string; mode?: string }) => {
    const response = await api.get<Project[]>('/projects', { params })
    return response.data
  },
  getSummaries: async () => {
    const response = await api.get<ProjectSummary[]>('/projects/summaries')
    return response.data
  },
  getReminders: async () => {
    const response = await api.get<ProjectReminder[]>('/projects/reminders')
    return response.data
  },
  getById: async (id: string) => {
    const response = await api.get<Project>(`/projects/${id}`)
    return response.data
  },
  create: async (data: { name: string; description?: string; target_date?: string; total_budget: number; mode: 'personal' | 'pro' }) => {
    const response = await api.post<Project>('/projects', data)
    return response.data
  },
  update: async (id: string, data: { name?: string; description?: string; target_date?: string; total_budget?: number; status?: string }) => {
    const response = await api.put<Project>(`/projects/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/projects/${id}`)
  },
  getCategories: async (projectId: string) => {
    const response = await api.get<ProjectCategoryWithSpent[]>(`/projects/${projectId}/categories`)
    return response.data
  },
  createCategory: async (projectId: string, data: { name: string; planned_amount: number }) => {
    const response = await api.post<ProjectCategory>(`/projects/${projectId}/categories`, data)
    return response.data
  },
  updateCategory: async (projectId: string, categoryId: string, data: { name?: string; planned_amount?: number }) => {
    const response = await api.put<ProjectCategory>(`/projects/${projectId}/categories/${categoryId}`, data)
    return response.data
  },
  deleteCategory: async (projectId: string, categoryId: string) => {
    await api.delete(`/projects/${projectId}/categories/${categoryId}`)
  },
  getPlannedExpenses: async (projectId: string) => {
    const response = await api.get<ProjectPlannedExpense[]>(`/projects/${projectId}/planned-expenses`)
    return response.data
  },
  createPlannedExpense: async (projectId: string, data: { project_category_id: string; description: string; amount: number; due_date?: string; reminder_date?: string }) => {
    const response = await api.post<ProjectPlannedExpense>(`/projects/${projectId}/planned-expenses`, data)
    return response.data
  },
  updatePlannedExpense: async (projectId: string, expenseId: string, data: {
    project_category_id?: string; description?: string; amount?: number;
    due_date?: string; reminder_date?: string; status?: string;
    transaction_id?: string; pro_transaction_id?: string
  }) => {
    const response = await api.put<ProjectPlannedExpense>(`/projects/${projectId}/planned-expenses/${expenseId}`, data)
    return response.data
  },
  deletePlannedExpense: async (projectId: string, expenseId: string) => {
    await api.delete(`/projects/${projectId}/planned-expenses/${expenseId}`)
  },
  getTransactions: async (projectId: string) => {
    const response = await api.get<ProjectTransaction[]>(`/projects/${projectId}/transactions`)
    return response.data
  },
  // Members
  getMembers: async (projectId: string) => {
    const response = await api.get<ProjectMemberWithUser[]>(`/projects/${projectId}/members`)
    return response.data
  },
  inviteMember: async (projectId: string, email: string, role: string = 'member') => {
    const response = await api.post(`/projects/${projectId}/members`, { email, role })
    return response.data
  },
  removeMember: async (projectId: string, memberId: string) => {
    await api.delete(`/projects/${projectId}/members/${memberId}`)
  },
  // Invitations
  getMyInvitations: async () => {
    const response = await api.get<ProjectInvitationWithDetails[]>('/projects/invitations/pending')
    return response.data
  },
  acceptInvitation: async (invitationId: string) => {
    const response = await api.post(`/projects/invitations/${invitationId}/accept`)
    return response.data
  },
  rejectInvitation: async (invitationId: string) => {
    const response = await api.post(`/projects/invitations/${invitationId}/reject`)
    return response.data
  },
}

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

  getMonthlyRecap: async () => {
    const response = await api.get<MonthlyRecap>('/budgets/monthly-recap')
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
// Monthly Recap Types
// ============================================================================

export interface TopCategory {
  name: string
  total: number
}

export interface MonthlyRecap {
  total_income: number
  total_expenses: number
  balance: number
  top_expense_categories: TopCategory[]
}

// ============================================================================
// Upcoming Recurring Types
// ============================================================================

export interface UpcomingRecurring {
  id: string
  title: string
  amount: number
  transaction_type: string
  expected_date: string
  category_name: string
  budget_name: string
  is_processed: boolean
}

// ============================================================================
// Loan Types
// ============================================================================

export interface LoanRepayment {
  id: string
  loan_id: string
  amount: number
  date: string
  comment: string | null
  created_at: string
}

export interface Loan {
  id: string
  user_id: string
  person_name: string
  amount: number
  direction: 'lent' | 'borrowed'
  date: string
  description: string | null
  status: 'active' | 'repaid'
  created_at: string
  updated_at: string
  total_repaid: number
  remaining: number
  repayments: LoanRepayment[]
}

export interface LoanSummary {
  total_lent: number
  total_borrowed: number
  total_lent_remaining: number
  total_borrowed_remaining: number
  net_position: number
}

// ============================================================================
// Project Types
// ============================================================================

export interface ProjectCategory {
  id: string
  project_id: string
  name: string
  planned_amount: number
  created_at: string
}

export interface ProjectCategoryWithSpent extends ProjectCategory {
  total_spent: number
  remaining: number
}

export interface Project {
  id: string
  user_id: string
  name: string
  description: string | null
  target_date: string | null
  total_budget: number
  status: 'active' | 'completed' | 'abandoned'
  mode: 'personal' | 'pro'
  created_at: string
  updated_at: string
  total_spent: number
  remaining: number
  categories: ProjectCategoryWithSpent[]
}

export interface ProjectPlannedExpense {
  id: string
  project_id: string
  project_category_id: string
  description: string
  amount: number
  due_date: string | null
  reminder_date: string | null
  status: 'pending' | 'paid'
  transaction_id: string | null
  pro_transaction_id: string | null
  created_at: string
  updated_at: string
  category_name: string | null
}

export interface ProjectSummary {
  id: string
  name: string
  mode: string
  status: string
  total_budget: number
  total_spent: number
  remaining: number
  percentage: number
  category_count: number
  planned_expense_count: number
  pending_expense_count: number
  target_date: string | null
}

export interface ProjectReminder {
  id: string
  project_id: string
  project_name: string
  description: string
  amount: number
  due_date: string | null
  reminder_date: string
  category_name: string | null
}

export interface ProjectTransaction {
  id: string
  title: string
  amount: number
  transaction_type: string
  date: string
  comment: string | null
  project_category_id: string
  category_name: string | null
  project_category_name: string | null
  source: 'personal' | 'pro'
  payer_user_id: string | null
  payer_name: string | null
  payer_email: string | null
  payer_avatar: string | null
}

export interface ProjectMemberWithUser {
  id: string
  project_id: string
  user_id: string
  role: string
  created_at: string
  user_name: string
  user_email: string
  user_avatar: string | null
}

export interface ProjectInvitationWithDetails {
  id: string
  project_id: string
  project_name: string
  inviter_id: string
  inviter_name: string
  invitee_email: string
  role: string
  status: string
  created_at: string
}

// ============================================================================
// Pro (Auto-Entrepreneur) Types
// ============================================================================

export type LegalForm = 'micro' | 'ei_reel' | 'eurl' | 'sasu' | 'sas'

export interface ProProfile {
  id: string
  user_id: string
  siret: string | null
  legal_form: LegalForm
  activity_type: string
  cotisation_rate: number
  declaration_frequency: string
  revenue_threshold: number
  cfp_rate: number | null
  versement_liberatoire_enabled: number
  versement_liberatoire_rate: number | null
  ir_abattement_rate: number | null
  foyer_tmi: number | null
  tns_cotisations_rate: number
  salary_gross_monthly: number
  dividends_yearly: number
  eurl_tax_option: 'ir' | 'is'
  is_subject_to_vat: number
  vat_rate: number
  vat_number: string | null
  company_name: string | null
  company_address: string | null
  company_email: string | null
  company_phone: string | null
  street: string | null
  postal_code: string | null
  city: string | null
  country: string
  acre_enabled: number
  acre_start_date: string | null
  created_at: string
  updated_at: string
}

export interface CotisationsDetail {
  maladie_maternite: number
  retraite_base: number
  retraite_complementaire: number
  invalidite_deces: number
  allocations_familiales: number
  csg_crds: number
}

export interface TaxBreakdown {
  legal_form: LegalForm
  period: 'month' | 'quarter' | 'year'
  period_label: string
  turnover: number
  deductible_expenses: number
  benefice_imposable: number | null
  cotisations_sociales: number
  cfp: number
  ir_versement_liberatoire: number | null
  ir_classique_estime: number | null
  impot_societes: number | null
  dividendes_taxes: number | null
  net_salary: number | null
  total_prelevements: number
  net_after_taxes: number
  personal_take_home: number
  notes: string[]
  cotisations_detail: CotisationsDetail | null
}

export interface ProClient {
  id: string
  user_id: string
  name: string
  email: string | null
  phone: string | null
  address: string | null
  notes: string | null
  siren: string | null
  siret: string | null
  vat_number: string | null
  street: string | null
  postal_code: string | null
  city: string | null
  country: string
  is_professional: number
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
  is_declared: number
  is_deductible: number
  vat_rate: number | null
  invoice_id: string | null
  project_category_id?: string | null
  created_at: string
  client_name: string | null
  category_name: string | null
  items: ProTransactionItem[]
}

export interface DeclarationPeriodSummary {
  period_start: string
  period_end: string
  period_label: string
  total_income: number
  declared_income: number
  undeclared_income: number
  total_transactions: number
  declared_transactions: number
  cotisations_estimated: number
}

export interface UrssafScheduleItem {
  period_label: string
  period_start: string
  period_end: string
  deadline: string
  days_remaining: number
  status: 'past' | 'current' | 'upcoming'
  turnover: number
  cotisations: number
  cfp: number
  ir_vl: number
  total_due: number
  is_projection: boolean
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
// Pro Invoice & Quote Types
// ============================================================================

export interface ProInvoiceSettings {
  id: string
  user_id: string
  invoice_prefix: string
  quote_prefix: string
  next_invoice_number: number
  next_quote_number: number
  payment_terms_days: number
  late_penalty_rate: number
  bank_name: string | null
  bank_iban: string | null
  bank_bic: string | null
  default_notes: string | null
  logo_path: string | null
  created_at: string
  updated_at: string
}

export interface ProInvoiceItem {
  id: string
  invoice_id: string
  product_id: string | null
  description: string
  quantity: number
  unit_price: number
  total: number
  sort_order: number
}

export interface ProInvoice {
  id: string
  user_id: string
  client_id: string
  invoice_number: string
  status: 'draft' | 'sent' | 'paid' | 'cancelled'
  issue_date: string
  due_date: string
  subtotal: number
  tva_rate: number
  tva_amount: number
  total: number
  discount_type: 'percentage' | 'fixed' | null
  discount_value: number
  notes: string | null
  payment_method: string | null
  paid_date: string | null
  quote_id: string | null
  reminder_sent_at: string | null
  created_at: string
  updated_at: string
  client_name: string | null
  client_email: string | null
  client_address: string | null
  items: ProInvoiceItem[]
}

export interface ProQuoteItem {
  id: string
  quote_id: string
  product_id: string | null
  description: string
  quantity: number
  unit_price: number
  total: number
  sort_order: number
}

export interface ProQuote {
  id: string
  user_id: string
  client_id: string
  quote_number: string
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired'
  issue_date: string
  validity_date: string
  subtotal: number
  tva_rate: number
  tva_amount: number
  total: number
  discount_type: 'percentage' | 'fixed' | null
  discount_value: number
  notes: string | null
  invoice_id: string | null
  created_at: string
  updated_at: string
  client_name: string | null
  client_email: string | null
  client_address: string | null
  items: ProQuoteItem[]
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
  getTaxBreakdown: async (period: 'month' | 'quarter' | 'year', year?: number) => {
    const response = await api.get<TaxBreakdown>('/pro/tax-breakdown', { params: { period, year } })
    return response.data
  },
  getRegimeComparison: async (period: 'month' | 'quarter' | 'year', year?: number) => {
    const response = await api.get<RegimeComparisonRow[]>('/pro/regime-comparison', { params: { period, year } })
    return response.data
  },
  getVatSummary: async (period: 'month' | 'quarter' | 'year', year?: number) => {
    const response = await api.get<VatSummary>('/pro/vat-summary', { params: { period, year } })
    return response.data
  },
}

export interface VatSummary {
  period: 'month' | 'quarter' | 'year'
  period_label: string
  is_subject_to_vat: number
  default_rate: number
  collected: number
  deductible: number
  balance: number
  notes: string[]
}

export interface RegimeComparisonRow {
  regime: 'micro' | 'ei_reel' | 'eurl_ir' | 'eurl_is' | 'sasu' | 'sas'
  breakdown: TaxBreakdown
}

export const proClientsAPI = {
  getAll: async () => {
    const response = await api.get<ProClient[]>('/pro/clients')
    return response.data
  },
  create: async (data: {
    name: string; email?: string; phone?: string; address?: string; notes?: string;
    siren?: string; siret?: string; vat_number?: string;
    street?: string; postal_code?: string; city?: string; country?: string; is_professional?: number;
  }) => {
    const response = await api.post<ProClient>('/pro/clients', data)
    return response.data
  },
  update: async (id: string, data: {
    name?: string; email?: string; phone?: string; address?: string; notes?: string;
    siren?: string; siret?: string; vat_number?: string;
    street?: string; postal_code?: string; city?: string; country?: string; is_professional?: number;
  }) => {
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
    project_category_id?: string | null
    is_declared?: number
    is_deductible?: number
    vat_rate?: number | null
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
    project_category_id?: string | null
    is_declared?: number
    is_deductible?: number
    vat_rate?: number | null
  }) => {
    const response = await api.put<ProTransaction>(`/pro/transactions/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/transactions/${id}`)
  },
}

export interface ProRecurringTransaction {
  id: string
  user_id: string
  client_id: string | null
  category_id: string
  title: string
  amount: number
  transaction_type: 'income' | 'expense'
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
  day: number | null
  payment_method: string | null
  comment: string | null
  active: number
  created_at: string
  client_name: string | null
  category_name: string | null
}

export const proRecurringAPI = {
  getAll: async () => {
    const response = await api.get<ProRecurringTransaction[]>('/pro/recurring')
    return response.data
  },
  create: async (data: {
    client_id?: string | null
    category_id: string
    title: string
    amount: number
    transaction_type: 'income' | 'expense'
    frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
    day?: number | null
    payment_method?: string
    comment?: string
  }) => {
    const response = await api.post<ProRecurringTransaction>('/pro/recurring', data)
    return response.data
  },
  update: async (id: string, data: Partial<{
    client_id: string | null
    category_id: string
    title: string
    amount: number
    transaction_type: 'income' | 'expense'
    frequency: 'daily' | 'weekly' | 'monthly' | 'yearly'
    day: number | null
    payment_method: string
    comment: string
    active: number
  }>) => {
    const response = await api.put<ProRecurringTransaction>(`/pro/recurring/${id}`, data)
    return response.data
  },
  toggle: async (id: string) => {
    const response = await api.put<ProRecurringTransaction>(`/pro/recurring/${id}/toggle`)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/recurring/${id}`)
  },
  process: async () => {
    const response = await api.post<ProTransaction[]>('/pro/recurring/process')
    return response.data
  },
}

export interface ProThreshold {
  id: string
  user_id: string
  name: string
  period: 'monthly' | 'quarterly' | 'yearly'
  amount: number
  color: string
  active: number
  created_at: string
}

export const proThresholdsAPI = {
  getAll: async () => {
    const response = await api.get<ProThreshold[]>('/pro/thresholds')
    return response.data
  },
  create: async (data: { name: string; period: 'monthly' | 'quarterly' | 'yearly'; amount: number; color?: string }) => {
    const response = await api.post<ProThreshold>('/pro/thresholds', data)
    return response.data
  },
  update: async (id: string, data: Partial<{ name: string; period: 'monthly' | 'quarterly' | 'yearly'; amount: number; color: string; active: number }>) => {
    const response = await api.put<ProThreshold>(`/pro/thresholds/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/thresholds/${id}`)
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

export const proDeclarationAPI = {
  getPeriods: async (year?: number) => {
    const response = await api.get<DeclarationPeriodSummary[]>('/pro/declaration/periods', { params: year ? { year } : {} })
    return response.data
  },
  batchToggleDeclared: async (transaction_ids: string[], is_declared: number) => {
    const response = await api.put('/pro/transactions/declare', { transaction_ids, is_declared })
    return response.data
  },
  getUrssafSchedule: async () => {
    const response = await api.get<UrssafScheduleItem[]>('/pro/urssaf/schedule')
    return response.data
  },
}

export const proInvoiceSettingsAPI = {
  get: async () => {
    const response = await api.get<ProInvoiceSettings>('/pro/invoice-settings')
    return response.data
  },
  update: async (data: Partial<ProInvoiceSettings>) => {
    const response = await api.put<ProInvoiceSettings>('/pro/invoice-settings', data)
    return response.data
  },
}

export const proInvoicesAPI = {
  getAll: async (params?: { status?: string; client_id?: string; start_date?: string; end_date?: string }) => {
    const response = await api.get<ProInvoice[]>('/pro/invoices', { params })
    return response.data
  },
  getById: async (id: string) => {
    const response = await api.get<ProInvoice>(`/pro/invoices/${id}`)
    return response.data
  },
  create: async (data: {
    client_id: string; issue_date: string; due_date: string;
    discount_type?: 'percentage' | 'fixed'; discount_value?: number; notes?: string;
    items: { product_id?: string; description: string; quantity: number; unit_price: number }[]
  }) => {
    const response = await api.post<ProInvoice>('/pro/invoices', data)
    return response.data
  },
  update: async (id: string, data: {
    client_id?: string; issue_date?: string; due_date?: string;
    discount_type?: 'percentage' | 'fixed'; discount_value?: number; notes?: string;
    items?: { product_id?: string; description: string; quantity: number; unit_price: number }[]
  }) => {
    const response = await api.put<ProInvoice>(`/pro/invoices/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/invoices/${id}`)
  },
  updateStatus: async (id: string, data: { status: string; payment_method?: string; paid_date?: string }) => {
    const response = await api.put<ProInvoice>(`/pro/invoices/${id}/status`, data)
    return response.data
  },
  markReminder: async (id: string) => {
    const response = await api.put<ProInvoice>(`/pro/invoices/${id}/reminder`)
    return response.data
  },
  sendEmail: async (id: string) => {
    const response = await api.post(`/pro/invoices/${id}/send-email`)
    return response.data
  },
  downloadPdf: async (id: string, facturx = false) => {
    const response = await api.get(`/pro/invoices/${id}/pdf`, {
      responseType: 'blob',
      params: { facturx },
    })
    return response.data
  },
  exportForPdp: async (id: string) => {
    const response = await api.get(`/pro/invoices/${id}/export`)
    return response.data
  },
}

export const proQuotesAPI = {
  getAll: async (params?: { status?: string; client_id?: string; start_date?: string; end_date?: string }) => {
    const response = await api.get<ProQuote[]>('/pro/quotes', { params })
    return response.data
  },
  getById: async (id: string) => {
    const response = await api.get<ProQuote>(`/pro/quotes/${id}`)
    return response.data
  },
  create: async (data: {
    client_id: string; issue_date: string; validity_date: string;
    discount_type?: 'percentage' | 'fixed'; discount_value?: number; notes?: string;
    items: { product_id?: string; description: string; quantity: number; unit_price: number }[]
  }) => {
    const response = await api.post<ProQuote>('/pro/quotes', data)
    return response.data
  },
  update: async (id: string, data: {
    client_id?: string; issue_date?: string; validity_date?: string;
    discount_type?: 'percentage' | 'fixed'; discount_value?: number; notes?: string;
    items?: { product_id?: string; description: string; quantity: number; unit_price: number }[]
  }) => {
    const response = await api.put<ProQuote>(`/pro/quotes/${id}`, data)
    return response.data
  },
  delete: async (id: string) => {
    await api.delete(`/pro/quotes/${id}`)
  },
  updateStatus: async (id: string, data: { status: string }) => {
    const response = await api.put<ProQuote>(`/pro/quotes/${id}/status`, data)
    return response.data
  },
  convertToInvoice: async (id: string) => {
    const response = await api.post<ProInvoice>(`/pro/quotes/${id}/convert-to-invoice`)
    return response.data
  },
  downloadPdf: async (id: string) => {
    const response = await api.get(`/pro/quotes/${id}/pdf`, { responseType: 'blob' })
    return response.data
  },
}

// ============================================================================
// Subscription Types
// ============================================================================

export interface Subscription {
  id: string
  user_id: string
  stripe_subscription_id: string | null
  stripe_price_id: string
  plan_type: 'monthly' | 'annual'
  status: 'active' | 'past_due' | 'canceled' | 'incomplete' | 'trialing'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  canceled_at: string | null
  created_at: string
  updated_at: string
}

export interface SubscriptionStatus {
  has_subscription: boolean
  subscription: Subscription | null
  plan_type: string | null
  status: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
}

export interface CheckoutResponse {
  checkout_url: string
  session_id: string
}

export interface PortalResponse {
  portal_url: string
}

// ============================================================================
// Admin Types
// ============================================================================

export interface AdminUserInfo {
  id: string
  email: string
  name: string
  is_admin: boolean
  pro_override: boolean
  created_at: string
  subscription: Subscription | null
}

export interface SubscriptionStats {
  total_users: number
  total_subscribers: number
  active_subscriptions: number
  monthly_subscribers: number
  annual_subscribers: number
  mrr: number
  arr: number
  churn_rate: number
}

export interface AdminQuote {
  id: string
  created_by_user_id: string
  prospect_name: string
  prospect_email: string
  prospect_company: string | null
  plan_type: 'monthly' | 'annual'
  quantity: number
  unit_price: number
  total: number
  valid_until: string
  notes: string | null
  status: 'draft' | 'sent' | 'accepted' | 'expired'
  created_at: string
  updated_at: string
}

// ============================================================================
// Stripe API Methods
// ============================================================================

export interface StripePrices {
  monthly: number
  annual: number
}

export const stripeAPI = {
  getPrices: async () => {
    const response = await api.get<StripePrices>('/stripe/prices')
    return response.data
  },

  createCheckout: async (data: { plan_type: 'monthly' | 'annual'; success_url: string; cancel_url: string }) => {
    const response = await api.post<CheckoutResponse>('/stripe/checkout', data)
    return response.data
  },

  getSubscription: async () => {
    const response = await api.get<SubscriptionStatus>('/stripe/subscription')
    return response.data
  },

  createPortalSession: async () => {
    const response = await api.post<PortalResponse>('/stripe/portal')
    return response.data
  },

  getProAccess: async () => {
    const response = await api.get<ProAccessStatus>('/stripe/pro-access')
    return response.data
  },
}

// ============================================================================
// Admin API Methods
// ============================================================================

export const adminAPI = {
  getUsers: async () => {
    const response = await api.get<AdminUserInfo[]>('/admin/users')
    return response.data
  },

  getUser: async (userId: string) => {
    const response = await api.get<AdminUserInfo>(`/admin/users/${userId}`)
    return response.data
  },

  getSubscriptions: async () => {
    const response = await api.get<Subscription[]>('/admin/subscriptions')
    return response.data
  },

  getSubscriptionStats: async () => {
    const response = await api.get<SubscriptionStats>('/admin/subscriptions/stats')
    return response.data
  },

  getQuotes: async () => {
    const response = await api.get<AdminQuote[]>('/admin/quotes')
    return response.data
  },

  createQuote: async (data: {
    prospect_name: string
    prospect_email: string
    prospect_company?: string
    plan_type: 'monthly' | 'annual'
    quantity?: number
    unit_price: number
    valid_days?: number
    notes?: string
  }) => {
    const response = await api.post<AdminQuote>('/admin/quotes', data)
    return response.data
  },

  getQuote: async (quoteId: string) => {
    const response = await api.get<AdminQuote>(`/admin/quotes/${quoteId}`)
    return response.data
  },

  updateQuote: async (quoteId: string, data: {
    prospect_name?: string
    prospect_email?: string
    prospect_company?: string
    plan_type?: 'monthly' | 'annual'
    quantity?: number
    unit_price?: number
    valid_until?: string
    notes?: string
    status?: 'draft' | 'sent' | 'accepted' | 'expired'
  }) => {
    const response = await api.put<AdminQuote>(`/admin/quotes/${quoteId}`, data)
    return response.data
  },

  deleteQuote: async (quoteId: string) => {
    await api.delete(`/admin/quotes/${quoteId}`)
  },

  downloadQuotePdf: async (quoteId: string, lang: 'fr' | 'en' = 'fr') => {
    const response = await api.get(`/admin/quotes/${quoteId}/pdf`, { params: { lang }, responseType: 'blob' })
    return response.data
  },

  // Invitations management
  getInvitations: async () => {
    const response = await api.get<Invitation[]>('/admin/invitations')
    return response.data
  },

  createInvitation: async (email: string) => {
    const response = await api.post<Invitation>('/admin/invitations', { email })
    return response.data
  },

  deleteInvitation: async (invitationId: string) => {
    await api.delete(`/admin/invitations/${invitationId}`)
  },

  // Pro override management
  setProOverride: async (userId: string, proOverride: boolean) => {
    const response = await api.put(`/admin/users/${userId}/pro-override`, { pro_override: proOverride })
    return response.data
  },
}

export default api