<template>
  <n-space vertical size="large">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
      <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('pro.clients.title') }}</h1>
      <n-button type="primary" @click="openCreateModal">{{ t('pro.clients.addClient') }}</n-button>
    </div>

    <n-empty v-if="proStore.proClients.length === 0" :description="t('pro.clients.noClients')" />

    <!-- Desktop Table -->
    <n-data-table
      v-if="!isMobile && proStore.proClients.length > 0"
      :columns="columns"
      :data="proStore.proClients"
      :row-key="(row: ProClient) => row.id"
    />

    <!-- Mobile Cards -->
    <n-space v-if="isMobile && proStore.proClients.length > 0" vertical>
      <n-card v-for="client in proStore.proClients" :key="client.id" size="small">
        <template #header>
          <a style="color: #63e2b7; cursor: pointer; text-decoration: none;" @click="goToClientHistory(client.id)">
            <strong>{{ client.name }}</strong>
          </a>
        </template>
        <template #header-extra>
          <n-space size="small">
            <n-button size="tiny" type="info" @click="goToClientHistory(client.id)">{{ t('nav.proHistory') }}</n-button>
            <n-button size="tiny" @click="openEditModal(client)">{{ t('common.edit') }}</n-button>
            <n-popconfirm @positive-click="handleDelete(client.id)">
              <template #trigger>
                <n-button size="tiny" type="error">{{ t('common.delete') }}</n-button>
              </template>
              {{ t('pro.clients.deleteClientConfirm') }}
            </n-popconfirm>
          </n-space>
        </template>
        <n-space vertical size="small">
          <span v-if="client.email">{{ client.email }}</span>
          <span v-if="client.phone">{{ client.phone }}</span>
          <span v-if="client.address" style="color: rgba(255,255,255,0.5); font-size: 12px;">{{ client.address }}</span>
        </n-space>
      </n-card>
    </n-space>

    <!-- Create/Edit Modal -->
    <n-modal v-model:show="showModal" preset="card" :title="editingClient ? t('pro.clients.editClient') : t('pro.clients.addClient')" style="max-width: 600px;">
      <n-form ref="formRef" :model="clientForm">
        <n-form-item :label="t('pro.clients.name')" path="name" :rule="{ required: true, message: t('errors.required') }">
          <n-input v-model:value="clientForm.name" />
        </n-form-item>
        <n-form-item :label="t('pro.clients.email')">
          <n-input v-model:value="clientForm.email" />
        </n-form-item>
        <n-form-item :label="t('pro.clients.phone')">
          <n-input v-model:value="clientForm.phone" />
        </n-form-item>

        <n-divider>{{ t('pro.clients.legalInfo') }}</n-divider>

        <n-form-item :label="t('pro.clients.clientType')">
          <n-radio-group v-model:value="clientForm.is_professional">
            <n-radio :value="1">{{ t('pro.clients.professional') }}</n-radio>
            <n-radio :value="0">{{ t('pro.clients.individual') }}</n-radio>
          </n-radio-group>
        </n-form-item>

        <template v-if="clientForm.is_professional === 1">
          <n-grid :cols="2" :x-gap="12">
            <n-gi>
              <n-form-item :label="t('pro.clients.siren')">
                <n-input v-model:value="clientForm.siren" placeholder="123456789" maxlength="9" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item :label="t('pro.clients.vatNumber')">
                <n-input v-model:value="clientForm.vat_number" placeholder="FR12345678901" />
              </n-form-item>
            </n-gi>
          </n-grid>
        </template>

        <n-divider>{{ t('pro.clients.addressSection') }}</n-divider>

        <n-form-item :label="t('pro.clients.street')">
          <n-input v-model:value="clientForm.street" :placeholder="t('placeholders.street')" />
        </n-form-item>
        <n-grid :cols="3" :x-gap="12">
          <n-gi>
            <n-form-item :label="t('pro.clients.postalCode')">
              <n-input v-model:value="clientForm.postal_code" placeholder="75001" maxlength="10" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.clients.city')">
              <n-input v-model:value="clientForm.city" placeholder="Paris" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item :label="t('pro.clients.country')">
              <n-input v-model:value="clientForm.country" placeholder="FR" maxlength="2" />
            </n-form-item>
          </n-gi>
        </n-grid>

        <n-form-item :label="t('pro.clients.notes')">
          <n-input v-model:value="clientForm.notes" type="textarea" :rows="2" />
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
  NInput, NEmpty, NPopconfirm, NDivider, NRadioGroup, NRadio, NGrid, NGi,
  useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useProStore } from '@/stores/pro'
import { useMobileDetect } from '@/composables/useMobileDetect'
import type { ProClient } from '@/services/api'

const { t } = useI18n()
const router = useRouter()
const proStore = useProStore()
const message = useMessage()
const { isMobile } = useMobileDetect()

function goToClientHistory(clientId: string) {
  router.push({ name: 'pro-history', query: { client_id: clientId } })
}

const showModal = ref(false)
const editingClient = ref<ProClient | null>(null)
const formRef = ref()

const clientForm = ref({
  name: '',
  email: '',
  phone: '',
  notes: '',
  siren: '',
  vat_number: '',
  street: '',
  postal_code: '',
  city: '',
  country: 'FR',
  is_professional: 1 as number,
})

const columns: DataTableColumns<ProClient> = [
  {
    title: () => t('pro.clients.name'),
    key: 'name',
    render(row) {
      return h('a', {
        style: 'color: #63e2b7; cursor: pointer; text-decoration: none;',
        onClick: () => goToClientHistory(row.id),
      }, row.name)
    },
  },
  { title: () => t('pro.clients.email'), key: 'email' },
  { title: () => t('pro.clients.phone'), key: 'phone' },
  { title: () => t('pro.clients.siren'), key: 'siren' },
  {
    title: () => t('pro.clients.city'),
    key: 'city',
    render: (row) => row.city ? `${row.postal_code || ''} ${row.city}`.trim() : '',
  },
  {
    title: () => t('common.actions'),
    key: 'actions',
    width: 200,
    render(row) {
      return h(NSpace, { size: 'small' }, () => [
        h(NButton, { size: 'small', type: 'info', onClick: () => goToClientHistory(row.id) }, () => t('nav.proHistory')),
        h(NButton, { size: 'small', onClick: () => openEditModal(row) }, () => t('common.edit')),
        h(NPopconfirm, { onPositiveClick: () => handleDelete(row.id) }, {
          trigger: () => h(NButton, { size: 'small', type: 'error' }, () => t('common.delete')),
          default: () => t('pro.clients.deleteClientConfirm'),
        }),
      ])
    },
  },
]

function openCreateModal() {
  editingClient.value = null
  clientForm.value = {
    name: '', email: '', phone: '', notes: '',
    siren: '', vat_number: '', street: '', postal_code: '', city: '', country: 'FR', is_professional: 1,
  }
  showModal.value = true
}

function openEditModal(client: ProClient) {
  editingClient.value = client
  clientForm.value = {
    name: client.name,
    email: client.email || '',
    phone: client.phone || '',
    notes: client.notes || '',
    siren: client.siren || '',
    vat_number: client.vat_number || '',
    street: client.street || '',
    postal_code: client.postal_code || '',
    city: client.city || '',
    country: client.country || 'FR',
    is_professional: client.is_professional ?? 1,
  }
  showModal.value = true
}

async function handleSubmit() {
  if (!clientForm.value.name.trim()) return

  const data = {
    name: clientForm.value.name,
    email: clientForm.value.email || undefined,
    phone: clientForm.value.phone || undefined,
    notes: clientForm.value.notes || undefined,
    siren: clientForm.value.siren || undefined,
    vat_number: clientForm.value.vat_number || undefined,
    street: clientForm.value.street || undefined,
    postal_code: clientForm.value.postal_code || undefined,
    city: clientForm.value.city || undefined,
    country: clientForm.value.country || undefined,
    is_professional: clientForm.value.is_professional,
  }

  if (editingClient.value) {
    await proStore.updateClient(editingClient.value.id, data)
    message.success(t('pro.clients.clientUpdated'))
  } else {
    await proStore.createClient(data)
    message.success(t('pro.clients.clientAdded'))
  }
  showModal.value = false
}

async function handleDelete(id: string) {
  await proStore.deleteClient(id)
  message.success(t('pro.clients.clientDeleted'))
}

onMounted(() => {
  proStore.fetchClients()
})
</script>
