import { ref } from 'vue'
import { defineStore } from 'pinia'
import { loansAPI, type Loan, type LoanSummary } from '@/services/api'

export const useLoanStore = defineStore('loan', () => {
  const loans = ref<Loan[]>([])
  const summary = ref<LoanSummary | null>(null)
  const loading = ref(false)

  const fetchLoans = async () => {
    loading.value = true
    try {
      loans.value = await loansAPI.getAll()
    } finally {
      loading.value = false
    }
  }

  const fetchSummary = async () => {
    summary.value = await loansAPI.getSummary()
  }

  const createLoan = async (data: { person_name: string; amount: number; direction: 'lent' | 'borrowed'; date: string; description?: string }) => {
    const loan = await loansAPI.create(data)
    loans.value.unshift(loan)
    await fetchSummary()
    return loan
  }

  const updateLoan = async (id: string, data: { person_name?: string; amount?: number; direction?: 'lent' | 'borrowed'; date?: string; description?: string; status?: 'active' | 'repaid' }) => {
    const updated = await loansAPI.update(id, data)
    const index = loans.value.findIndex(l => l.id === id)
    if (index !== -1) loans.value[index] = updated
    await fetchSummary()
    return updated
  }

  const deleteLoan = async (id: string) => {
    await loansAPI.delete(id)
    loans.value = loans.value.filter(l => l.id !== id)
    await fetchSummary()
  }

  const addRepayment = async (loanId: string, data: { amount: number; date: string; comment?: string }) => {
    await loansAPI.addRepayment(loanId, data)
    // Refresh the loan to get updated totals
    await fetchLoans()
    await fetchSummary()
  }

  const deleteRepayment = async (loanId: string, repaymentId: string) => {
    await loansAPI.deleteRepayment(loanId, repaymentId)
    await fetchLoans()
    await fetchSummary()
  }

  return {
    loans, summary, loading,
    fetchLoans, fetchSummary, createLoan, updateLoan, deleteLoan,
    addRepayment, deleteRepayment,
  }
})
