<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Admin Users View

  User management with subscription status.
-->

<template>
  <n-space vertical size="large">
    <n-flex justify="space-between" align="center" wrap>
      <h1 class="page-title">{{ t('admin.users') }}</h1>
      <n-input
        v-model:value="searchQuery"
        :placeholder="t('admin.searchUsers')"
        clearable
        style="max-width: 300px;"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>
    </n-flex>

    <n-spin :show="loading">
      <n-data-table
        :columns="columns"
        :data="filteredUsers"
        :pagination="pagination"
        :row-key="(row) => row.id"
      />
    </n-spin>

    <!-- User Detail Modal -->
    <n-modal v-model:show="showUserModal">
      <n-card
        :title="selectedUser?.name"
        :bordered="false"
        size="huge"
        class="user-modal"
      >
        <n-descriptions :column="1" bordered v-if="selectedUser">
          <n-descriptions-item :label="t('admin.email')">
            {{ selectedUser.email }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('admin.isAdmin')">
            <n-tag :type="selectedUser.is_admin ? 'success' : 'default'">
              {{ selectedUser.is_admin ? t('common.yes') : t('common.no') }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item :label="t('admin.createdAt')">
            {{ formatDate(selectedUser.created_at) }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('admin.subscriptionStatus')">
            <n-tag v-if="selectedUser.subscription" :type="getStatusType(selectedUser.subscription.status)">
              {{ t(`subscription.statuses.${selectedUser.subscription.status}`) }}
            </n-tag>
            <n-text v-else depth="3">{{ t('admin.noSubscription') }}</n-text>
          </n-descriptions-item>
          <n-descriptions-item v-if="selectedUser.subscription" :label="t('admin.plan')">
            {{ selectedUser.subscription.plan_type === 'annual' ? t('subscription.annual') : t('subscription.monthly') }}
          </n-descriptions-item>
          <n-descriptions-item v-if="selectedUser.subscription" :label="t('admin.periodEnd')">
            {{ formatDate(selectedUser.subscription.current_period_end) }}
          </n-descriptions-item>
        </n-descriptions>

        <template #footer>
          <n-button @click="showUserModal = false">{{ t('common.close') }}</n-button>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NSpace, NFlex, NCard, NButton, NDataTable, NInput, NIcon, NTag,
  NText, NModal, NDescriptions, NDescriptionsItem, NSpin,
  type DataTableColumns
} from 'naive-ui'
import { SearchOutline, EyeOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import { adminAPI, type AdminUserInfo } from '@/services/api'

const { t, locale } = useI18n()

const loading = ref(false)
const users = ref<AdminUserInfo[]>([])
const searchQuery = ref('')
const showUserModal = ref(false)
const selectedUser = ref<AdminUserInfo | null>(null)

const pagination = {
  pageSize: 20,
}

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(u =>
    u.name.toLowerCase().includes(query) ||
    u.email.toLowerCase().includes(query)
  )
})

const getStatusType = (status: string) => {
  switch (status) {
    case 'active':
    case 'trialing':
      return 'success'
    case 'past_due':
      return 'warning'
    case 'canceled':
      return 'error'
    default:
      return 'default'
  }
}

const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const columns = computed<DataTableColumns<AdminUserInfo>>(() => [
  {
    title: t('admin.name'),
    key: 'name',
    sorter: 'default',
  },
  {
    title: t('admin.email'),
    key: 'email',
    sorter: 'default',
  },
  {
    title: t('admin.subscription'),
    key: 'subscription',
    render: (row) => {
      const sub = row.subscription
      if (!sub) {
        return h(NText, { depth: 3 }, () => t('admin.noSubscription'))
      }
      return h(NTag, { type: getStatusType(sub.status), size: 'small' }, () =>
        `${sub.plan_type === 'annual' ? t('subscription.annual') : t('subscription.monthly')} - ${t(`subscription.statuses.${sub.status}`)}`
      )
    },
  },
  {
    title: t('admin.admin'),
    key: 'is_admin',
    width: 80,
    render: (row) => h(NTag, {
      type: row.is_admin ? 'success' : 'default',
      size: 'small'
    }, () => row.is_admin ? t('common.yes') : t('common.no')),
  },
  {
    title: t('admin.createdAt'),
    key: 'created_at',
    sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    render: (row) => formatDate(row.created_at),
  },
  {
    title: t('common.actions'),
    key: 'actions',
    width: 100,
    render: (row) => h(NButton, {
      size: 'small',
      quaternary: true,
      onClick: () => {
        selectedUser.value = row
        showUserModal.value = true
      }
    }, {
      icon: () => h(NIcon, { component: EyeOutline }),
    }),
  },
])

onMounted(async () => {
  loading.value = true
  try {
    users.value = await adminAPI.getUsers()
  } catch (error) {
    console.error('Error loading users:', error)
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

.user-modal {
  width: 500px;
  max-width: 95vw;
}
</style>
