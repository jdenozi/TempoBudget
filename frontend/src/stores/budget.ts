/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Budget Store
 *
 * Pinia store for managing budget-related state and operations.
 * Provides centralized state management for budgets, categories,
 * transactions, and recurring transactions.
 *
 * State:
 * - budgets: List of all user budgets
 * - currentBudget: Currently selected budget
 * - categories: Categories for the current budget
 * - transactions: Transactions for the current budget
 * - recurringTransactions: Recurring transactions for the current budget
 * - loading: Loading state indicator
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { budgetsAPI, categoriesAPI, transactionsAPI, recurringAPI, type Budget, type Category, type Transaction, type RecurringTransaction } from '@/services/api'

export const useBudgetStore = defineStore('budget', () => {
  /** List of all user budgets */
  const budgets = ref<Budget[]>([])

  /** Currently selected budget */
  const currentBudget = ref<Budget | null>(null)

  /** Categories for the current budget */
  const categories = ref<Category[]>([])

  /** Transactions for the current budget */
  const transactions = ref<Transaction[]>([])

  /** Recurring transactions for the current budget */
  const recurringTransactions = ref<RecurringTransaction[]>([])

  /** Loading state indicator */
  const loading = ref(false)

  // ============================================================================
  // Budget Operations
  // ============================================================================

  /**
   * Fetches all budgets for the current user.
   */
  async function fetchBudgets() {
    loading.value = true
    try {
      budgets.value = await budgetsAPI.getAll()
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetches a specific budget by ID and sets it as the current budget.
   * @param id - Budget unique identifier
   */
  async function fetchBudget(id: string) {
    loading.value = true
    try {
      currentBudget.value = await budgetsAPI.getById(id)
    } finally {
      loading.value = false
    }
  }

  /**
   * Creates a new budget and adds it to the local state.
   * @param name - Budget name
   * @param budget_type - Either 'personal' or 'group'
   * @returns The created budget
   */
  async function createBudget(name: string, budget_type: string) {
    const budget = await budgetsAPI.create(name, budget_type)
    budgets.value.push(budget)
    return budget
  }

  // ============================================================================
  // Category Operations
  // ============================================================================

  /**
   * Fetches all categories for a specific budget.
   * @param budgetId - Budget unique identifier
   */
  async function fetchCategories(budgetId: string) {
    loading.value = true
    try {
      categories.value = await categoriesAPI.getByBudget(budgetId)
    } finally {
      loading.value = false
    }
  }

  /**
   * Creates a new category and adds it to the local state.
   * @param budgetId - Budget unique identifier
   * @param name - Category name
   * @param amount - Allocated amount
   * @returns The created category
   */
  async function createCategory(budgetId: string, name: string, amount: number, parentId?: string, tags?: string[]) {
    const category = await categoriesAPI.create(budgetId, name, amount, parentId, tags)
    categories.value.push(category)
    return category
  }

  /**
   * Updates an existing category and updates the local state.
   * @param id - Category unique identifier
   * @param data - Fields to update
   * @returns The updated category
   */
  async function updateCategory(id: string, data: { name?: string; amount?: number; tags?: string[] }) {
    const updated = await categoriesAPI.update(id, data)
    const index = categories.value.findIndex(c => c.id === id)
    if (index !== -1) {
      categories.value[index] = updated
    }
    return updated
  }

  /**
   * Deletes a category and removes it from the local state.
   * @param id - Category unique identifier
   */
  async function deleteCategory(id: string) {
    await categoriesAPI.delete(id)
    categories.value = categories.value.filter(c => c.id !== id)
  }

  // ============================================================================
  // Transaction Operations
  // ============================================================================

  /**
   * Fetches all transactions for a specific budget.
   * @param budgetId - Budget unique identifier
   */
  async function fetchTransactions(budgetId: string) {
    loading.value = true
    try {
      transactions.value = await transactionsAPI.getByBudget(budgetId)
    } finally {
      loading.value = false
    }
  }

  /**
   * Creates a new transaction and adds it to the local state.
   * @param data - Transaction data
   * @returns The created transaction
   */
  async function createTransaction(data: {
    budget_id: string
    category_id: string
    title: string
    amount: number
    transaction_type: string
    date: string
    comment?: string
    paid_by_user_id?: string
  }) {
    const transaction = await transactionsAPI.create(data)
    transactions.value.unshift(transaction)
    return transaction
  }

  /**
   * Deletes a transaction and removes it from the local state.
   * @param id - Transaction unique identifier
   */
  async function deleteTransaction(id: string) {
    await transactionsAPI.delete(id)
    transactions.value = transactions.value.filter(t => t.id !== id)
  }

  // ============================================================================
  // Recurring Transaction Operations
  // ============================================================================

  /**
   * Fetches all recurring transactions for a specific budget.
   * @param budgetId - Budget unique identifier
   */
  async function fetchRecurringTransactions(budgetId: string) {
    loading.value = true
    try {
      recurringTransactions.value = await recurringAPI.getByBudget(budgetId)
    } finally {
      loading.value = false
    }
  }

  /**
   * Creates a new recurring transaction and adds it to the local state.
   * @param data - Recurring transaction data
   * @returns The created recurring transaction
   */
  async function createRecurringTransaction(data: {
    budget_id: string
    category_id: string
    title: string
    amount: number
    transaction_type: string
    frequency: string
    day?: number
  }) {
    const recurring = await recurringAPI.create(data)
    recurringTransactions.value.push(recurring)
    return recurring
  }

  /**
   * Toggles the active status of a recurring transaction.
   * @param id - Recurring transaction unique identifier
   * @returns The updated recurring transaction
   */
  async function toggleRecurringTransaction(id: string) {
    const updated = await recurringAPI.toggle(id)
    const index = recurringTransactions.value.findIndex(r => r.id === id)
    if (index !== -1) {
      recurringTransactions.value[index] = updated
    }
    return updated
  }

  /**
   * Deletes a recurring transaction and removes it from the local state.
   * @param id - Recurring transaction unique identifier
   */
  async function deleteRecurringTransaction(id: string) {
    await recurringAPI.delete(id)
    recurringTransactions.value = recurringTransactions.value.filter(r => r.id !== id)
  }

  return {
    budgets,
    currentBudget,
    categories,
    transactions,
    recurringTransactions,
    loading,
    fetchBudgets,
    fetchBudget,
    createBudget,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    fetchTransactions,
    createTransaction,
    deleteTransaction,
    fetchRecurringTransactions,
    createRecurringTransaction,
    toggleRecurringTransaction,
    deleteRecurringTransaction,
  }
})