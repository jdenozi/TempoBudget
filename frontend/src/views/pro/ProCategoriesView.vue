<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.categories.title') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.categories.addCategory') }}</n-button>
    </div>

    <!-- Filter Tabs -->
    <n-tabs type="segment" v-model:value="activeTab">
      <n-tab-pane name="all" :tab="t('pro.categories.all')" />
      <n-tab-pane name="income" :tab="t('transaction.income')" />
      <n-tab-pane name="expense" :tab="t('transaction.expense')" />
    </n-tabs>

    <!-- Category List -->
    <n-empty v-if="filteredCategories.length === 0" :description="t('pro.categories.noCategories')" />
    <n-space v-else vertical :size="8">
      <n-card v-for="cat in filteredCategories" :key="cat.id" size="small">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-weight: 500;">{{ cat.name }}</span>
            <n-tag size="small" :type="cat.type === 'income' ? 'success' : 'error'">
              {{ cat.type === 'income' ? t('transaction.income') : t('transaction.expense') }}
            </n-tag>
            <n-tag v-if="cat.is_default" size="tiny" type="info">{{ t('pro.categories.default') }}</n-tag>
          </div>
          <n-space :size="4">
            <n-button size="small" @click="openEditModal(cat)">{{ t('common.edit') }}</n-button>
            <n-popconfirm v-if="!cat.is_default" @positive-click="handleDelete(cat)">
              <template #trigger>
                <n-button size="small" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('pro.categories.deleteCategoryConfirm') }}
            </n-popconfirm>
          </n-space>
        </div>
      </n-card>
    </n-space>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editing ? t('pro.categories.editCategory') : t('pro.categories.addCategory')" style="max-width: 400px;">
      <n-form :model="form">
        <n-form-item :label="t('pro.categories.name')">
          <n-input v-model:value="form.name" :placeholder="t('pro.categories.name')" />
        </n-form-item>
        <n-form-item :label="t('transaction.type')">
          <n-radio-group v-model:value="form.type">
            <n-radio-button value="income">{{ t('transaction.income') }}</n-radio-button>
            <n-radio-button value="expense">{{ t('transaction.expense') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-button type="primary" block @click="handleSubmit" :loading="saving">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NSpace, NButton, NCard, NTabs, NTabPane, NTag, NEmpty,
  NModal, NForm, NFormItem, NInput, NRadioGroup, NRadioButton,
  NPopconfirm, useMessage,
} from 'naive-ui'
import { useProStore } from '@/stores/pro'
import type { ProCategory } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()

const activeTab = ref('all')
const showModal = ref(false)
const editing = ref<ProCategory | null>(null)
const saving = ref(false)

const form = ref({
  name: '',
  type: 'expense' as 'income' | 'expense',
})

const filteredCategories = computed(() => {
  if (activeTab.value === 'income') return proStore.proCategories.filter(c => c.type === 'income')
  if (activeTab.value === 'expense') return proStore.proCategories.filter(c => c.type === 'expense')
  return proStore.proCategories
})

function openCreateModal() {
  editing.value = null
  form.value = { name: '', type: 'expense' }
  showModal.value = true
}

function openEditModal(cat: ProCategory) {
  editing.value = cat
  form.value = { name: cat.name, type: cat.type as 'income' | 'expense' }
  showModal.value = true
}

async function handleSubmit() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    if (editing.value) {
      await proStore.updateCategory(editing.value.id, form.value)
      message.success(t('pro.categories.categoryUpdated'))
    } else {
      await proStore.createCategory(form.value)
      message.success(t('pro.categories.categoryAdded'))
    }
    showModal.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete(cat: ProCategory) {
  if (cat.is_default) {
    message.warning(t('pro.categories.cannotDeleteDefault'))
    return
  }
  await proStore.deleteCategory(cat.id)
  message.success(t('pro.categories.categoryDeleted'))
}

onMounted(async () => {
  await proStore.fetchCategories()
})
</script>
