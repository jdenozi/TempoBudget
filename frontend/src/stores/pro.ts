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
  proCouponsAPI, proGiftCardsAPI, proInvoicesAPI, proQuotesAPI, proInvoiceSettingsAPI, proDeclarationAPI,
  proRecurringAPI, proThresholdsAPI,
  type ProProfile, type ProClient, type ProCategory, type ProTransaction, type ProDashboardSummary, type ProProduct,
  type ProCoupon, type ProGiftCard, type ProGiftCardUsage,
  type ProInvoice, type ProQuote, type ProInvoiceSettings, type DeclarationPeriodSummary,
  type ProRecurringTransaction, type ProThreshold,
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

  /** Pro invoices */
  const proInvoices = ref<ProInvoice[]>([])

  /** Pro quotes */
  const proQuotes = ref<ProQuote[]>([])

  /** Pro recurring transactions */
  const proRecurring = ref<ProRecurringTransaction[]>([])

  /** User-defined revenue thresholds */
  const proThresholds = ref<ProThreshold[]>([])

  /** Invoice settings */
  const invoiceSettings = ref<ProInvoiceSettings | null>(null)

  /** Dashboard summary */
  const dashboardSummary = ref<ProDashboardSummary | null>(null)

  /** Declaration periods */
  const declarationPeriods = ref<DeclarationPeriodSummary[]>([])

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
    project_category_id?: string | null
    is_declared?: number
    is_deductible?: number
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
    project_category_id?: string | null
    is_declared?: number
    is_deductible?: number
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

  // ── Invoice Settings ──

  async function fetchInvoiceSettings() {
    invoiceSettings.value = await proInvoiceSettingsAPI.get()
  }

  async function updateInvoiceSettings(data: Partial<ProInvoiceSettings>) {
    invoiceSettings.value = await proInvoiceSettingsAPI.update(data)
  }

  // ── Invoices ──

  async function fetchInvoices(params?: { status?: string; client_id?: string; start_date?: string; end_date?: string }) {
    loading.value = true
    try {
      proInvoices.value = await proInvoicesAPI.getAll(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchInvoice(id: string) {
    return await proInvoicesAPI.getById(id)
  }

  async function createInvoice(data: Parameters<typeof proInvoicesAPI.create>[0]) {
    const inv = await proInvoicesAPI.create(data)
    proInvoices.value.unshift(inv)
    return inv
  }

  async function updateInvoice(id: string, data: Parameters<typeof proInvoicesAPI.update>[1]) {
    const updated = await proInvoicesAPI.update(id, data)
    const idx = proInvoices.value.findIndex(i => i.id === id)
    if (idx !== -1) proInvoices.value[idx] = updated
    return updated
  }

  async function deleteInvoice(id: string) {
    await proInvoicesAPI.delete(id)
    proInvoices.value = proInvoices.value.filter(i => i.id !== id)
  }

  async function updateInvoiceStatus(id: string, data: { status: string; payment_method?: string; paid_date?: string }) {
    const updated = await proInvoicesAPI.updateStatus(id, data)
    const idx = proInvoices.value.findIndex(i => i.id === id)
    if (idx !== -1) proInvoices.value[idx] = updated
    return updated
  }

  async function markInvoiceReminder(id: string) {
    const updated = await proInvoicesAPI.markReminder(id)
    const idx = proInvoices.value.findIndex(i => i.id === id)
    if (idx !== -1) proInvoices.value[idx] = updated
    return updated
  }

  async function downloadInvoicePdf(id: string) {
    return await proInvoicesAPI.downloadPdf(id)
  }

  // ── Quotes ──

  async function fetchQuotes(params?: { status?: string; client_id?: string; start_date?: string; end_date?: string }) {
    loading.value = true
    try {
      proQuotes.value = await proQuotesAPI.getAll(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchQuote(id: string) {
    return await proQuotesAPI.getById(id)
  }

  async function createQuote(data: Parameters<typeof proQuotesAPI.create>[0]) {
    const q = await proQuotesAPI.create(data)
    proQuotes.value.unshift(q)
    return q
  }

  async function updateQuote(id: string, data: Parameters<typeof proQuotesAPI.update>[1]) {
    const updated = await proQuotesAPI.update(id, data)
    const idx = proQuotes.value.findIndex(q => q.id === id)
    if (idx !== -1) proQuotes.value[idx] = updated
    return updated
  }

  async function deleteQuote(id: string) {
    await proQuotesAPI.delete(id)
    proQuotes.value = proQuotes.value.filter(q => q.id !== id)
  }

  async function updateQuoteStatus(id: string, data: { status: string }) {
    const updated = await proQuotesAPI.updateStatus(id, data)
    const idx = proQuotes.value.findIndex(q => q.id === id)
    if (idx !== -1) proQuotes.value[idx] = updated
    return updated
  }

  async function convertQuoteToInvoice(id: string) {
    const invoice = await proQuotesAPI.convertToInvoice(id)
    proInvoices.value.unshift(invoice)
    // Refresh quotes to get updated invoice_id link
    await fetchQuotes()
    return invoice
  }

  async function downloadQuotePdf(id: string) {
    return await proQuotesAPI.downloadPdf(id)
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

  // ── Declaration ──

  async function fetchDeclarationPeriods(year?: number) {
    declarationPeriods.value = await proDeclarationAPI.getPeriods(year)
  }

  async function batchToggleDeclared(transactionIds: string[], isDeclared: number) {
    await proDeclarationAPI.batchToggleDeclared(transactionIds, isDeclared)
  }

  // ── Recurring transactions ──

  async function fetchRecurring() {
    proRecurring.value = await proRecurringAPI.getAll()
  }

  async function createRecurring(data: Parameters<typeof proRecurringAPI.create>[0]) {
    const rec = await proRecurringAPI.create(data)
    proRecurring.value.unshift(rec)
    return rec
  }

  async function updateRecurring(id: string, data: Parameters<typeof proRecurringAPI.update>[1]) {
    const updated = await proRecurringAPI.update(id, data)
    const idx = proRecurring.value.findIndex(r => r.id === id)
    if (idx !== -1) proRecurring.value[idx] = updated
    return updated
  }

  async function toggleRecurring(id: string) {
    const updated = await proRecurringAPI.toggle(id)
    const idx = proRecurring.value.findIndex(r => r.id === id)
    if (idx !== -1) proRecurring.value[idx] = updated
    return updated
  }

  async function deleteRecurring(id: string) {
    await proRecurringAPI.delete(id)
    proRecurring.value = proRecurring.value.filter(r => r.id !== id)
  }

  async function processRecurring() {
    const created = await proRecurringAPI.process()
    if (created.length > 0) {
      proTransactions.value.unshift(...created)
    }
    return created
  }

  // ── Thresholds ──

  async function fetchThresholds() {
    proThresholds.value = await proThresholdsAPI.getAll()
  }

  async function createThreshold(data: Parameters<typeof proThresholdsAPI.create>[0]) {
    const t = await proThresholdsAPI.create(data)
    proThresholds.value.unshift(t)
    return t
  }

  async function updateThreshold(id: string, data: Parameters<typeof proThresholdsAPI.update>[1]) {
    const updated = await proThresholdsAPI.update(id, data)
    const idx = proThresholds.value.findIndex(t => t.id === id)
    if (idx !== -1) proThresholds.value[idx] = updated
    return updated
  }

  async function deleteThreshold(id: string) {
    await proThresholdsAPI.delete(id)
    proThresholds.value = proThresholds.value.filter(t => t.id !== id)
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
    proInvoices,
    proQuotes,
    invoiceSettings,
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
    // Invoice Settings
    fetchInvoiceSettings,
    updateInvoiceSettings,
    // Invoices
    fetchInvoices,
    fetchInvoice,
    createInvoice,
    updateInvoice,
    deleteInvoice,
    updateInvoiceStatus,
    markInvoiceReminder,
    downloadInvoicePdf,
    // Quotes
    fetchQuotes,
    fetchQuote,
    createQuote,
    updateQuote,
    deleteQuote,
    updateQuoteStatus,
    convertQuoteToInvoice,
    downloadQuotePdf,
    // Dashboard
    fetchDashboard,
    // Declaration
    declarationPeriods,
    fetchDeclarationPeriods,
    batchToggleDeclared,
    // Recurring
    proRecurring,
    fetchRecurring,
    createRecurring,
    updateRecurring,
    toggleRecurring,
    deleteRecurring,
    processRecurring,
    // Thresholds
    proThresholds,
    fetchThresholds,
    createThreshold,
    updateThreshold,
    deleteThreshold,
  }
})
