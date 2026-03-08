/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Pro Store
 *
 * Pinia store for managing pro (auto-entrepreneur) state and operations.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  proProfileAPI, proClientsAPI, proCategoriesAPI, proTransactionsAPI, proDashboardAPI, proProductsAPI,
  proCouponsAPI, proGiftCardsAPI,
  type ProProfile, type ProClient, type ProCategory, type ProTransaction, type ProDashboardSummary, type ProProduct,
  type ProCoupon, type ProGiftCard, type ProGiftCardUsage,
} from '@/services/api'

export const useProStore = defineStore('pro', () => {
  /** Whether pro mode is active */
  const isProMode = ref(false)

  /** Pro profile */
  const proProfile = ref<ProProfile | null>(null)

  /** Pro clients */
  const proClients = ref<ProClient[]>([])

  /** Pro categories */
  const proCategories = ref<ProCategory[]>([])

  /** Pro transactions */
  const proTransactions = ref<ProTransaction[]>([])

  /** Pro products/services catalogue */
  const proProducts = ref<ProProduct[]>([])

  /** Pro coupons */
  const proCoupons = ref<ProCoupon[]>([])

  /** Pro gift cards */
  const proGiftCards = ref<ProGiftCard[]>([])

  /** Dashboard summary */
  const dashboardSummary = ref<ProDashboardSummary | null>(null)

  /** Loading state */
  const loading = ref(false)

  // ── Mode toggle ──

  function initProMode() {
    const saved = localStorage.getItem('pro_mode')
    if (saved) {
      isProMode.value = JSON.parse(saved)
    }
  }

  function setProMode(value: boolean) {
    isProMode.value = value
    localStorage.setItem('pro_mode', JSON.stringify(value))
  }

  // ── Profile ──

  async function fetchProfile() {
    loading.value = true
    try {
      proProfile.value = await proProfileAPI.get()
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: Partial<ProProfile>) {
    proProfile.value = await proProfileAPI.update(data)
  }

  // ── Clients ──

  async function fetchClients() {
    proClients.value = await proClientsAPI.getAll()
  }

  async function createClient(data: { name: string; email?: string; phone?: string; address?: string; notes?: string }) {
    const client = await proClientsAPI.create(data)
    proClients.value.push(client)
    return client
  }

  async function updateClient(id: string, data: { name?: string; email?: string; phone?: string; address?: string; notes?: string }) {
    const updated = await proClientsAPI.update(id, data)
    const idx = proClients.value.findIndex(c => c.id === id)
    if (idx !== -1) proClients.value[idx] = updated
    return updated
  }

  async function deleteClient(id: string) {
    await proClientsAPI.delete(id)
    proClients.value = proClients.value.filter(c => c.id !== id)
  }

  // ── Categories ──

  async function fetchCategories() {
    proCategories.value = await proCategoriesAPI.getAll()
  }

  async function createCategory(data: { name: string; type: 'income' | 'expense' }) {
    const cat = await proCategoriesAPI.create(data)
    proCategories.value.push(cat)
    return cat
  }

  async function updateCategory(id: string, data: { name?: string; type?: 'income' | 'expense' }) {
    const updated = await proCategoriesAPI.update(id, data)
    const idx = proCategories.value.findIndex(c => c.id === id)
    if (idx !== -1) proCategories.value[idx] = updated
    return updated
  }

  async function deleteCategory(id: string) {
    await proCategoriesAPI.delete(id)
    proCategories.value = proCategories.value.filter(c => c.id !== id)
  }

  // ── Products ──

  async function fetchProducts() {
    proProducts.value = await proProductsAPI.getAll()
  }

  async function createProduct(data: { name: string; type: 'product' | 'service'; default_price: number; category_id?: string }) {
    const product = await proProductsAPI.create(data)
    proProducts.value.push(product)
    return product
  }

  async function updateProduct(id: string, data: { name?: string; type?: 'product' | 'service'; default_price?: number; category_id?: string }) {
    const updated = await proProductsAPI.update(id, data)
    const idx = proProducts.value.findIndex(p => p.id === id)
    if (idx !== -1) proProducts.value[idx] = updated
    return updated
  }

  async function deleteProduct(id: string) {
    await proProductsAPI.delete(id)
    proProducts.value = proProducts.value.filter(p => p.id !== id)
  }

  // ── Coupons ──

  async function fetchCoupons() {
    proCoupons.value = await proCouponsAPI.getAll()
  }

  async function createCoupon(data: {
    code: string; name: string; discount_type: 'percentage' | 'fixed';
    discount_value: number; valid_from?: string; valid_until?: string; max_uses?: number
  }) {
    const coupon = await proCouponsAPI.create(data)
    proCoupons.value.unshift(coupon)
    return coupon
  }

  async function updateCoupon(id: string, data: {
    code?: string; name?: string; discount_type?: 'percentage' | 'fixed';
    discount_value?: number; valid_from?: string; valid_until?: string;
    max_uses?: number; is_active?: number
  }) {
    const updated = await proCouponsAPI.update(id, data)
    const idx = proCoupons.value.findIndex(c => c.id === id)
    if (idx !== -1) proCoupons.value[idx] = updated
    return updated
  }

  async function deleteCoupon(id: string) {
    await proCouponsAPI.delete(id)
    proCoupons.value = proCoupons.value.filter(c => c.id !== id)
  }

  // ── Gift Cards ──

  async function fetchGiftCards() {
    proGiftCards.value = await proGiftCardsAPI.getAll()
  }

  async function createGiftCard(data: { code: string; initial_amount: number; client_id?: string; purchase_date: string }) {
    const gc = await proGiftCardsAPI.create(data)
    proGiftCards.value.unshift(gc)
    return gc
  }

  async function fetchGiftCardUsages(id: string) {
    return await proGiftCardsAPI.getUsages(id)
  }

  async function deleteGiftCard(id: string) {
    await proGiftCardsAPI.delete(id)
    proGiftCards.value = proGiftCards.value.filter(gc => gc.id !== id)
  }

  // ── Transactions ──

  async function fetchTransactions(params?: { start_date?: string; end_date?: string; client_id?: string; category_id?: string; payment_method?: string; product_id?: string }) {
    loading.value = true
    try {
      proTransactions.value = await proTransactionsAPI.getAll(params)
    } finally {
      loading.value = false
    }
  }

  async function createTransaction(data: {
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
  }) {
    const tx = await proTransactionsAPI.create(data)
    proTransactions.value.unshift(tx)
    return tx
  }

  async function updateTransaction(id: string, data: {
    client_id?: string
    category_id?: string
    title?: string
    amount?: number
    transaction_type?: 'income' | 'expense'
    date?: string
    payment_method?: string
    comment?: string
  }) {
    const updated = await proTransactionsAPI.update(id, data)
    const idx = proTransactions.value.findIndex(t => t.id === id)
    if (idx !== -1) proTransactions.value[idx] = updated
    return updated
  }

  async function deleteTransaction(id: string) {
    await proTransactionsAPI.delete(id)
    proTransactions.value = proTransactions.value.filter(t => t.id !== id)
  }

  // ── Dashboard ──

  async function fetchDashboard() {
    loading.value = true
    try {
      dashboardSummary.value = await proDashboardAPI.getSummary()
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    isProMode,
    proProfile,
    proClients,
    proCategories,
    proProducts,
    proCoupons,
    proGiftCards,
    proTransactions,
    dashboardSummary,
    loading,
    // Mode
    initProMode,
    setProMode,
    // Profile
    fetchProfile,
    updateProfile,
    // Clients
    fetchClients,
    createClient,
    updateClient,
    deleteClient,
    // Categories
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    // Products
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    // Coupons
    fetchCoupons,
    createCoupon,
    updateCoupon,
    deleteCoupon,
    // Gift Cards
    fetchGiftCards,
    createGiftCard,
    fetchGiftCardUsages,
    deleteGiftCard,
    // Transactions
    fetchTransactions,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    // Dashboard
    fetchDashboard,
  }
})
