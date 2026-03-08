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
    <n-modal v-model:show="showModal" preset="card" :title="editingClient ? t('pro.clients.editClient') : t('pro.clients.addClient')" style="max-width: 500px;">
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
        <n-form-item :label="t('pro.clients.address')">
          <n-input v-model:value="clientForm.address" type="textarea" :rows="2" />
        </n-form-item>
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
  NInput, NEmpty, NPopconfirm, useMessage
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
  address: '',
  notes: '',
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
  { title: () => t('pro.clients.address'), key: 'address', ellipsis: { tooltip: true } },
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
  clientForm.value = { name: '', email: '', phone: '', address: '', notes: '' }
  showModal.value = true
}

function openEditModal(client: ProClient) {
  editingClient.value = client
  clientForm.value = {
    name: client.name,
    email: client.email || '',
    phone: client.phone || '',
    address: client.address || '',
    notes: client.notes || '',
  }
  showModal.value = true
}

async function handleSubmit() {
  if (!clientForm.value.name.trim()) return

  const data = {
    name: clientForm.value.name,
    email: clientForm.value.email || undefined,
    phone: clientForm.value.phone || undefined,
    address: clientForm.value.address || undefined,
    notes: clientForm.value.notes || undefined,
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
