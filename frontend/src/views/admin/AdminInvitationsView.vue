<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Admin Invitations View

  Invitation management for user registration.
-->

<template>
  <n-space vertical size="large">
    <n-flex justify="space-between" align="center" wrap>
      <h1 class="page-title">{{ t('admin.invitations') }}</h1>
      <n-button type="primary" @click="showCreateModal = true">
        {{ t('admin.createInvitation') }}
      </n-button>
    </n-flex>

    <n-spin :show="loading">
      <n-data-table
        :columns="columns"
        :data="invitations"
        :pagination="pagination"
        :row-key="(row) => row.id"
      />
    </n-spin>

    <!-- Create Invitation Modal -->
    <n-modal v-model:show="showCreateModal" @after-leave="resetForm">
      <n-card
        :title="t('admin.createInvitation')"
        :bordered="false"
        size="huge"
        class="invitation-modal"
      >
        <n-form ref="formRef" :model="invitationForm" :rules="rules">
          <n-form-item :label="t('admin.email')" path="email">
            <n-input v-model:value="invitationForm.email" placeholder="email@example.com" />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateModal = false">{{ t('common.cancel') }}</n-button>
            <n-button type="primary" :loading="saving" @click="handleCreate">
              {{ t('common.create') }}
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- Invitation Link Modal -->
    <n-modal v-model:show="showLinkModal">
      <n-card
        :title="t('admin.invitationLink')"
        :bordered="false"
        size="huge"
        class="invitation-modal"
      >
        <n-alert type="success" style="margin-bottom: 16px;">
          {{ t('admin.invitationCreated') }}
        </n-alert>

        <n-input-group>
          <n-input :value="invitationLink" readonly />
          <n-button type="primary" @click="copyLink">
            {{ t('admin.copyLink') }}
          </n-button>
        </n-input-group>

        <template #footer>
          <n-button @click="showLinkModal = false">{{ t('common.close') }}</n-button>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NSpace, NFlex, NCard, NButton, NDataTable, NInput, NInputGroup, NTag,
  NModal, NSpin, NForm, NFormItem, NAlert, NPopconfirm, useMessage,
  type DataTableColumns
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { adminAPI, type Invitation } from '@/services/api'

const { t, locale } = useI18n()
const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const invitations = ref<Invitation[]>([])
const showCreateModal = ref(false)
const showLinkModal = ref(false)
const invitationLink = ref('')
const formRef = ref<any>(null)

const pagination = {
  pageSize: 20,
}

const invitationForm = ref({
  email: '',
})

const rules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { type: 'email' as const, message: 'Invalid email format', trigger: 'blur' },
  ],
}

const resetForm = () => {
  invitationForm.value = { email: '' }
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getStatusType = (invitation: Invitation) => {
  if (invitation.used_at) return 'success'
  if (new Date(invitation.expires_at) < new Date()) return 'error'
  return 'warning'
}

const getStatusLabel = (invitation: Invitation) => {
  if (invitation.used_at) return t('admin.invitationUsed')
  if (new Date(invitation.expires_at) < new Date()) return t('admin.invitationExpired')
  return t('admin.invitationPending')
}

const columns = computed<DataTableColumns<Invitation>>(() => [
  {
    title: t('admin.email'),
    key: 'email',
    sorter: 'default',
  },
  {
    title: t('admin.status'),
    key: 'status',
    render: (row) => h(NTag, {
      type: getStatusType(row),
      size: 'small'
    }, () => getStatusLabel(row)),
  },
  {
    title: t('admin.createdAt'),
    key: 'created_at',
    sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    render: (row) => formatDate(row.created_at),
  },
  {
    title: t('admin.expiresAt'),
    key: 'expires_at',
    render: (row) => formatDate(row.expires_at),
  },
  {
    title: t('admin.usedAt'),
    key: 'used_at',
    render: (row) => row.used_at ? formatDate(row.used_at) : '—',
  },
  {
    title: t('common.actions'),
    key: 'actions',
    width: 180,
    render: (row) => {
      const buttons = []

      // Copy link button (only for pending invitations)
      if (!row.used_at && new Date(row.expires_at) >= new Date()) {
        buttons.push(h(NButton, {
          size: 'small',
          onClick: () => {
            const baseUrl = window.location.origin
            invitationLink.value = `${baseUrl}/login?token=${row.token}`
            showLinkModal.value = true
          }
        }, () => t('admin.copyLink')))
      }

      // Delete button
      buttons.push(h(NPopconfirm, {
        onPositiveClick: () => handleDelete(row.id),
      }, {
        trigger: () => h(NButton, {
          size: 'small',
          type: 'error',
          secondary: true,
          style: 'margin-left: 8px;'
        }, () => t('common.delete')),
        default: () => t('admin.confirmDeleteInvitation'),
      }))

      return buttons
    },
  },
])

const handleCreate = async () => {
  formRef.value?.validate(async (errors: any) => {
    if (errors) return

    saving.value = true
    try {
      const invitation = await adminAPI.createInvitation(invitationForm.value.email)
      invitations.value.unshift(invitation)
      showCreateModal.value = false

      // Show link modal
      const baseUrl = window.location.origin
      invitationLink.value = `${baseUrl}/login?token=${invitation.token}`
      showLinkModal.value = true

      message.success(t('admin.invitationCreatedSuccess'))
    } catch (error: any) {
      console.error('Error creating invitation:', error)
      message.error(t('common.error'))
    } finally {
      saving.value = false
    }
  })
}

const handleDelete = async (id: string) => {
  try {
    await adminAPI.deleteInvitation(id)
    invitations.value = invitations.value.filter(i => i.id !== id)
    message.success(t('admin.invitationDeleted'))
  } catch (error) {
    console.error('Error deleting invitation:', error)
    message.error(t('common.error'))
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(invitationLink.value)
    message.success(t('admin.linkCopied'))
  } catch {
    message.error(t('common.error'))
  }
}

onMounted(async () => {
  loading.value = true
  try {
    invitations.value = await adminAPI.getInvitations()
  } catch (error) {
    console.error('Error loading invitations:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}

.invitation-modal {
  width: 500px;
  max-width: 95vw;
}
</style>
