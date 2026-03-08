<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.coupons.title') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.coupons.addCoupon') }}</n-button>
    </div>

    <n-empty v-if="proStore.proCoupons.length === 0" :description="t('pro.coupons.noCoupons')" />

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile && proStore.proCoupons.length > 0"
      :columns="columns"
      :data="proStore.proCoupons"
      :row-key="(row: ProCoupon) => row.id"
    />

    <!-- Mobile Cards -->
    <n-space v-if="isMobile && proStore.proCoupons.length > 0" vertical>
      <n-card v-for="coupon in proStore.proCoupons" :key="coupon.id" size="small">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>{{ coupon.name }}</strong>
            <n-tag :type="coupon.is_active ? 'success' : 'default'" size="small">
              {{ coupon.is_active ? t('pro.coupons.active') : t('pro.coupons.inactive') }}
            </n-tag>
          </div>
        </template>
        <n-space size="small" style="margin-bottom: 8px;">
          <n-tag size="tiny" type="info">{{ coupon.code }}</n-tag>
          <n-tag size="tiny" :type="coupon.discount_type === 'percentage' ? 'warning' : 'success'">
            {{ coupon.discount_type === 'percentage' ? `${coupon.discount_value}%` : `${coupon.discount_value.toFixed(2)} €` }}
          </n-tag>
          <span style="font-size: 12px; color: rgba(255,255,255,0.5);">
            {{ coupon.max_uses > 0 ? `${coupon.used_count}/${coupon.max_uses}` : `${coupon.used_count} (${t('pro.coupons.unlimited')})` }}
          </span>
        </n-space>
        <div v-if="coupon.valid_from || coupon.valid_until" style="font-size: 12px; color: rgba(255,255,255,0.5);">
          <span v-if="coupon.valid_from">{{ t('pro.coupons.validFrom') }}: {{ coupon.valid_from }}</span>
          <span v-if="coupon.valid_from && coupon.valid_until"> — </span>
          <span v-if="coupon.valid_until">{{ t('pro.coupons.validUntil') }}: {{ coupon.valid_until }}</span>
        </div>
        <template #action>
          <n-space size="small">
            <n-button size="tiny" @click="openEditModal(coupon)">{{ t('common.edit') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(coupon.id)">
              <template #trigger>
                <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('pro.coupons.deleteCouponConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
      </n-card>
    </n-space>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingCoupon ? t('pro.coupons.editCoupon') : t('pro.coupons.addCoupon')" style="max-width: 500px;">
      <n-form :model="couponForm">
        <n-form-item :label="t('pro.coupons.name')">
          <n-input v-model:value="couponForm.name" />
        </n-form-item>
        <n-form-item :label="t('pro.coupons.code')">
          <n-input v-model:value="couponForm.code" />
        </n-form-item>
        <n-form-item :label="t('pro.coupons.discountType')">
          <n-radio-group v-model:value="couponForm.discount_type">
            <n-radio-button value="percentage">{{ t('pro.coupons.percentage') }}</n-radio-button>
            <n-radio-button value="fixed">{{ t('pro.coupons.fixed') }}</n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('pro.coupons.discountValue')">
          <n-input-number v-model:value="couponForm.discount_value" :min="0.01" :precision="2" style="width: 100%;">
            <template #suffix>{{ couponForm.discount_type === 'percentage' ? '%' : '€' }}</template>
          </n-input-number>
        </n-form-item>
        <n-form-item :label="t('pro.coupons.validFrom')">
          <n-date-picker v-model:value="couponForm.valid_from" type="date" style="width: 100%;" clearable />
        </n-form-item>
        <n-form-item :label="t('pro.coupons.validUntil')">
          <n-date-picker v-model:value="couponForm.valid_until" type="date" style="width: 100%;" clearable />
        </n-form-item>
        <n-form-item :label="t('pro.coupons.maxUses')">
          <n-input-number v-model:value="couponForm.max_uses" :min="0" style="width: 100%;">
            <template #suffix>{{ couponForm.max_uses === 0 ? t('pro.coupons.unlimited') : '' }}</template>
          </n-input-number>
        </n-form-item>
        <n-form-item v-if="editingCoupon" :label="t('common.status')">
          <n-switch v-model:value="couponForm.is_active" :checked-value="1" :unchecked-value="0">
            <template #checked>{{ t('pro.coupons.active') }}</template>
            <template #unchecked>{{ t('pro.coupons.inactive') }}</template>
          </n-switch>
        </n-form-item>
        <n-button type="primary" block @click="handleSubmit">{{ t('common.save') }}</n-button>
      </n-form>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import {
  NSpace, NCard, NButton, NDataTable, NModal, NForm, NFormItem,
  NInput, NInputNumber, NSelect, NRadioGroup, NRadioButton,
  NEmpty, NTag, NPopconfirm, NDatePicker, NSwitch, useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProCoupon } from '@/services/api'

const { t } = useI18n()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

const showModal = ref(false)
const editingCoupon = ref<ProCoupon | null>(null)

const couponForm = ref({
  name: '',
  code: '',
  discount_type: 'percentage' as 'percentage' | 'fixed',
  discount_value: 10 as number | null,
  valid_from: null as number | null,
  valid_until: null as number | null,
  max_uses: 0,
  is_active: 1,
})

function formatDate(ts: number) {
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const columns: DataTableColumns<ProCoupon> = [
  { title: () => t('pro.coupons.code'), key: 'code', width: 120 },
  { title: () => t('pro.coupons.name'), key: 'name' },
  {
    title: () => t('pro.coupons.discountValue'),
    key: 'discount_value',
    width: 130,
    render(row) {
      return row.discount_type === 'percentage'
        ? `${row.discount_value}%`
        : `${row.discount_value.toFixed(2)} €`
    },
  },
  {
    title: () => t('pro.coupons.usedCount'),
    key: 'used_count',
    width: 120,
    render(row) {
      return row.max_uses > 0 ? `${row.used_count}/${row.max_uses}` : `${row.used_count}`
    },
  },
  {
    title: () => t('pro.coupons.validUntil'),
    key: 'valid_until',
    width: 120,
  },
  {
    title: () => t('common.status'),
    key: 'is_active',
    width: 100,
    render(row) {
      return h(NTag, { size: 'small', type: row.is_active ? 'success' : 'default' },
        () => row.is_active ? t('pro.coupons.active') : t('pro.coupons.inactive'))
    },
  },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 150,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => t('common.edit')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.coupons.deleteCouponConfirm'),
        }),
      ])
    },
  },
]

function openCreateModal() {
  editingCoupon.value = null
  couponForm.value = {
    name: '', code: '', discount_type: 'percentage',
    discount_value: 10, valid_from: null, valid_until: null, max_uses: 0, is_active: 1,
  }
  showModal.value = true
}

function openEditModal(coupon: ProCoupon) {
  editingCoupon.value = coupon
  couponForm.value = {
    name: coupon.name,
    code: coupon.code,
    discount_type: coupon.discount_type,
    discount_value: coupon.discount_value,
    valid_from: coupon.valid_from ? new Date(coupon.valid_from).getTime() : null,
    valid_until: coupon.valid_until ? new Date(coupon.valid_until).getTime() : null,
    max_uses: coupon.max_uses,
    is_active: coupon.is_active,
  }
  showModal.value = true
}

async function handleSubmit() {
  if (!couponForm.value.name.trim() || !couponForm.value.code.trim()) return
  if (!couponForm.value.discount_value || couponForm.value.discount_value <= 0) return

  const data = {
    name: couponForm.value.name,
    code: couponForm.value.code,
    discount_type: couponForm.value.discount_type,
    discount_value: couponForm.value.discount_value,
    valid_from: couponForm.value.valid_from ? formatDate(couponForm.value.valid_from) : undefined,
    valid_until: couponForm.value.valid_until ? formatDate(couponForm.value.valid_until) : undefined,
    max_uses: couponForm.value.max_uses,
  }

  if (editingCoupon.value) {
    await proStore.updateCoupon(editingCoupon.value.id, { ...data, is_active: couponForm.value.is_active })
    message.success(t('pro.coupons.couponUpdated'))
  } else {
    await proStore.createCoupon(data)
    message.success(t('pro.coupons.couponAdded'))
  }
  showModal.value = false
}

async function handleDelete(id: string) {
  await proStore.deleteCoupon(id)
  message.success(t('pro.coupons.couponDeleted'))
}

onMounted(async () => {
  await proStore.fetchCoupons()
})
</script>
