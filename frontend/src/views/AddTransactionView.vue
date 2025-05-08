<template>
  <n-drawer-content title="Nouvelle transaction" closable>
    <n-form ref="formRef" :model="transaction" :rules="rules">
      <n-form-item label="Type" path="type">
        <n-radio-group v-model:value="transaction.type">
          <n-space>
            <n-radio value="expense">
              <n-tag type="error">Dépense</n-tag>
            </n-radio>
            <n-radio value="income">
              <n-tag type="success">Revenu</n-tag>
            </n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <n-form-item label="Catégorie" path="categoryId">
        <n-select
          v-model:value="transaction.categoryId"
          :options="categoryOptions"
          placeholder="Sélectionner une catégorie"
        />
      </n-form-item>

      <n-form-item label="Montant" path="amount">
        <n-input-number
          v-model:value="transaction.amount"
          :min="0"
          :precision="2"
          class="full-width"
        >
          <template #suffix>€</template>
        </n-input-number>
      </n-form-item>

      <n-form-item label="Titre" path="title">
        <n-input v-model:value="transaction.title" placeholder="Ex: Courses du mois" />
      </n-form-item>

      <n-form-item label="Date" path="date">
        <n-date-picker
          v-model:value="transaction.date"
          type="date"
          class="full-width"
        />
      </n-form-item>

      <n-form-item label="Commentaire (optionnel)">
        <n-input
          v-model:value="transaction.comment"
          type="textarea"
          placeholder="Ajouter un commentaire..."
          :rows="3"
        />
      </n-form-item>

      <n-form-item>
        <n-checkbox v-model:checked="transaction.isRecurring">
          Transaction récurrente
        </n-checkbox>
      </n-form-item>

      <n-collapse-transition :show="transaction.isRecurring">
        <n-space vertical>
          <n-form-item label="Fréquence" path="recurringFrequency">
            <n-select
              v-model:value="transaction.recurringFrequency"
              :options="FREQUENCY_OPTIONS"
              placeholder="Sélectionner la fréquence"
            />
          </n-form-item>

          <n-form-item v-if="transaction.recurringFrequency === 'monthly'" label="Jour du mois">
            <n-input-number
              v-model:value="transaction.recurringDay"
              :min="1"
              :max="31"
              class="full-width"
            />
          </n-form-item>
        </n-space>
      </n-collapse-transition>
    </n-form>

    <template #footer>
      <n-space justify="end">
        <n-button @click="emit('close')">Annuler</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          Ajouter
        </n-button>
      </n-space>
    </template>
  </n-drawer-content>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { FormInst, FormRules } from 'naive-ui'
import {
  NDrawerContent, NForm, NFormItem, NInput, NInputNumber, NSelect,
  NDatePicker, NCheckbox, NRadioGroup, NRadio, NTag, NButton,
  NSpace, NCollapseTransition, useMessage
} from 'naive-ui'
import { useBudgetStore } from '@/stores/budget'
import { recurringAPI } from '@/services/api'

type TransactionType = 'expense' | 'income'
type RecurringFrequency = 'monthly' | 'weekly' | 'yearly'

interface TransactionForm {
  type: TransactionType
  categoryId: string | null
  amount: number
  title: string
  date: number
  comment: string
  isRecurring: boolean
  recurringFrequency: RecurringFrequency
  recurringDay: number
}

const FREQUENCY_OPTIONS = [
  { label: 'Mensuelle', value: 'monthly' },
  { label: 'Hebdomadaire', value: 'weekly' },
  { label: 'Annuelle', value: 'yearly' },
] as const

const createInitialForm = (categoryId: string | null = null): TransactionForm => ({
  type: 'expense',
  categoryId,
  amount: 0,
  title: '',
  date: Date.now(),
  comment: '',
  isRecurring: false,
  recurringFrequency: 'monthly',
  recurringDay: 1,
})

const emit = defineEmits<{
  close: []
  success: []
}>()

const message = useMessage()
const budgetStore = useBudgetStore()

const loading = ref(false)
const formRef = ref<FormInst | null>(null)
const transaction = ref<TransactionForm>(createInitialForm())

const rules: FormRules = {
  categoryId: {
    required: true,
    message: 'Catégorie requise',
    trigger: 'change',
  },
  amount: {
    required: true,
    type: 'number',
    trigger: 'blur',
    validator: (_rule, value: number) => {
      if (!value || value <= 0) {
        return new Error('Le montant doit être supérieur à 0')
      }
      return true
    },
  },
  title: {
    required: true,
    message: 'Titre requis',
    trigger: 'blur',
  },
  date: {
    required: true,
    type: 'number',
    message: 'Date requise',
    trigger: 'change',
  },
}

const categoryOptions = computed(() =>
  budgetStore.categories.map(c => ({
    label: c.name,
    value: c.id,
  }))
)

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (!budgetStore.currentBudget) {
    message.error('Aucun budget sélectionné')
    return
  }

  loading.value = true
  try {
    const dateString = new Date(transaction.value.date).toISOString().split('T')[0]

    if (transaction.value.isRecurring) {
      await recurringAPI.create({
        budget_id: budgetStore.currentBudget.id,
        category_id: transaction.value.categoryId!,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        frequency: transaction.value.recurringFrequency,
        day: transaction.value.recurringFrequency === 'monthly'
          ? transaction.value.recurringDay
          : undefined,
      })
      message.success('Récurrence créée !')
    } else {
      await budgetStore.createTransaction({
        budget_id: budgetStore.currentBudget.id,
        category_id: transaction.value.categoryId!,
        title: transaction.value.title,
        amount: transaction.value.amount,
        transaction_type: transaction.value.type,
        date: dateString,
        comment: transaction.value.comment || undefined,
      })
      message.success('Transaction ajoutée !')
    }

    transaction.value = createInitialForm(budgetStore.categories[0]?.id ?? null)
    emit('success')
    emit('close')
  } catch (error) {
    console.error('Error creating transaction:', error)
    message.error('Erreur lors de la création')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (budgetStore.categories.length > 0) {
    transaction.value.categoryId = budgetStore.categories[0].id
  }
})
</script>

<style scoped>
.full-width {
  width: 100%;
}
</style>
