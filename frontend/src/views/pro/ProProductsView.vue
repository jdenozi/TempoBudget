<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.products.title') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.products.addProduct') }}</n-button>
    </div>

    <n-empty v-if="proStore.proProducts.length === 0" :description="t('pro.products.noProducts')" />

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile && proStore.proProducts.length > 0"
      :columns="columns"
      :data="proStore.proProducts"
      :row-key="(row: ProProduct) => row.id"
    />

    <!-- Mobile Cards -->
    <n-space v-if="isMobile && proStore.proProducts.length > 0" vertical>
      <n-card v-for="product in proStore.proProducts" :key="product.id" size="small">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>{{ product.name }}</strong>
            <span style="font-weight: bold;">{{ product.default_price.toFixed(2) }} €</span>
          </div>
        </template>
        <template #header-extra>
          <n-space size="small">
            <n-button size="tiny" @click="openEditModal(product)">{{ t('common.edit') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(product.id)">
              <template #trigger>
                <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('pro.products.deleteProductConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
        <n-space size="small">
          <n-tag size="tiny" :type="product.type === 'service' ? 'info' : product.type === 'gift_card' ? 'success' : 'warning'">
            {{ t(`pro.products.${product.type}`) }}
          </n-tag>
          <n-tag v-if="product.category_name" size="tiny">{{ product.category_name }}</n-tag>
        </n-space>
      </n-card>
    </n-space>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingProduct ? t('pro.products.editProduct') : t('pro.products.addProduct')" style="max-width: 500px;">
      <n-form :model="productForm">
        <n-form-item :label="t('pro.products.name')" :rule="{ required: true, message: t('errors.required') }">
          <n-input v-model:value="productForm.name" />
        </n-form-item>
        <n-form-item :label="t('pro.products.type')">
          <n-radio-group v-model:value="productForm.type">
            <n-radio-button value="service">{{ t('pro.products.service') }}</n-radio-button>
            <n-radio-button value="product">{{ t('pro.products.product') }}</n-radio-button>
            <n-radio-button value="gift_card">{{ t('pro.products.gift_card') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('pro.products.defaultPrice')">
          <n-input-number v-model:value="productForm.default_price" :min="0" :precision="2" style="width: 100%;">
            <template #suffix>€</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('pro.products.category')">
          <n-select v-model:value="productForm.category_id" :options="categoryOptions" clearable :placeholder="t('placeholders.selectCategory')" />
        </n-form-item>
        <n-button type="primary" block @click="handleSubmit">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NSpace, NCard, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NRadioGroup, NRadioButton,
  NEmpty, NTag, NPopconfirm, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProProduct } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const showModal = ref(false)
const editingProduct = ref<ProProduct | null>(null)

const productForm = ref({
  name: '',
  type: 'service' as 'product' | 'service' | 'gift_card',
  default_price: 0 as number | null,
  category_id: null as string | null,
})

const categoryOptions = computed(() =>
  proStore.proCategories.map(c => ({ label: `${c.name} (${c.type})`, value: c.id }))
)

const columns: DataTableColumns<ProProduct> = [
  { title: () => t('pro.products.name'), key: 'name' },
  {
    title: () => t('pro.products.type'),
    key: 'type',
    width: 120,
    render(row) {
      const typeMap = { service: 'info', product: 'warning', gift_card: 'success' } as const
      return h(NTag, { size: 'small', type: typeMap[row.type] || 'default' }, () => t(`pro.products.${row.type}`))
    },
  },
  {
    title: () => t('pro.products.defaultPrice'),
    key: 'default_price',
    width: 130,
    render(row) {
      return `${row.default_price.toFixed(2)} €`
    },
  },
  { title: () => t('pro.products.category'), key: 'category_name', width: 180 },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 150,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => t('common.edit')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.products.deleteProductConfirm'),
        }),
      ])
    },
  },
]

function openCreateModal() {
  editingProduct.value = null
  productForm.value = { name: '', type: 'service', default_price: 0, category_id: null }
  showModal.value = true
}

function openEditModal(product: ProProduct) {
  editingProduct.value = product
  productForm.value = {
    name: product.name,
    type: product.type,
    default_price: product.default_price,
    category_id: product.category_id,
  }
  showModal.value = true
}

async function handleSubmit() {
  if (!productForm.value.name.trim()) return

  const data = {
    name: productForm.value.name,
    type: productForm.value.type,
    default_price: productForm.value.default_price || 0,
    category_id: productForm.value.category_id || undefined,
  }

  if (editingProduct.value) {
    await proStore.updateProduct(editingProduct.value.id, data)
    message.success(t('pro.products.productUpdated'))
  } else {
    await proStore.createProduct(data)
    message.success(t('pro.products.productAdded'))
  }
  showModal.value = false
}

async function handleDelete(id: string) {
  await proStore.deleteProduct(id)
  message.success(t('pro.products.productDeleted'))
}

onMounted(async () => {
  await Promise.all([
    proStore.fetchProducts(),
    proStore.fetchCategories(),
  ])
})
</script>
