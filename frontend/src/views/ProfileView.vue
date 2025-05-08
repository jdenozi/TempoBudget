<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Profile View

  User profile management page displaying:
  - Personal information
  - Usage statistics
  - Pending budget invitations
  - Security settings
  - Account actions (logout, delete)
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">My Profile</h1>

    <!-- User Information -->
    <n-card title="Personal Information">
      <n-space vertical size="large">
        <!-- Avatar -->
        <div style="display: flex; align-items: center; gap: 16px;">
          <n-avatar
            :size="isMobile ? 80 : 100"
            round
            :src="authStore.user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${authStore.user?.name}`"
          />
          <n-button size="small" disabled>Change Photo</n-button>
        </div>

        <!-- User Details (read-only for now) -->
        <n-descriptions :column="1" bordered>
          <n-descriptions-item label="Name">
            {{ authStore.user?.name }}
          </n-descriptions-item>
          <n-descriptions-item label="Email">
            {{ authStore.user?.email }}
          </n-descriptions-item>
          <n-descriptions-item label="Phone">
            {{ authStore.user?.phone || 'Not provided' }}
          </n-descriptions-item>
          <n-descriptions-item label="Member since">
            {{ formatDate(authStore.user?.created_at) }}
          </n-descriptions-item>
        </n-descriptions>
      </n-space>
    </n-card>

    <!-- Statistics -->
    <n-card title="My Statistics">
      <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-statistic label="Active Budgets" :value="budgetStore.budgets.length" />
        </n-gi>
        <n-gi>
          <n-statistic label="Transactions this month" :value="transactionsThisMonth" />
        </n-gi>
        <n-gi>
          <n-statistic label="Categories" :value="totalCategories" />
        </n-gi>
        <n-gi>
          <n-statistic label="Recurring" :value="totalRecurring" />
        </n-gi>
      </n-grid>
    </n-card>

    <!-- Pending Invitations -->
    <n-card title="Pending Invitations" v-if="invitations.length > 0">
      <n-space vertical>
        <n-alert
          v-for="invitation in invitations"
          :key="invitation.id"
          type="info"
          closable
          @close="handleRejectInvitation(invitation.id)"
        >
          <template #header>
            Invitation to budget "{{ invitation.budget_name }}"
          </template>

          <div style="margin-bottom: 12px;">
            <strong>{{ invitation.inviter_name }}</strong> invites you to join this budget as
            <n-tag :type="invitation.role === 'owner' ? 'success' : 'default'" size="small">
              {{ invitation.role === 'owner' ? 'Owner' : 'Member' }}
            </n-tag>
          </div>

          <n-space>
            <n-button
              type="success"
              size="small"
              :loading="processingInvitation === invitation.id"
              @click="handleAcceptInvitation(invitation.id)"
            >
              Accept
            </n-button>
            <n-button
              size="small"
              :loading="processingInvitation === invitation.id"
              @click="handleRejectInvitation(invitation.id)"
            >
              Decline
            </n-button>
          </n-space>
        </n-alert>
      </n-space>
    </n-card>

    <!-- Security -->
    <n-card title="Security">
      <n-space vertical>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-weight: 500;">Password</div>
            <n-text depth="3">Manage your password</n-text>
          </div>
          <n-button size="small" disabled>Change Password</n-button>
        </div>

        <n-divider />

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-weight: 500;">Two-Factor Authentication</div>
            <n-text depth="3">Enhance your account security</n-text>
          </div>
          <n-button size="small" disabled>Enable</n-button>
        </div>
      </n-space>
    </n-card>

    <!-- Danger Zone -->
    <n-card title="Danger Zone">
      <n-space vertical>
        <n-alert type="warning" title="Irreversible Actions">
          The actions below are permanent and cannot be undone.
        </n-alert>

        <n-space :vertical="isMobile">
          <n-button disabled>Export My Data</n-button>

          <n-popconfirm @positive-click="handleDeleteAccount">
            <template #trigger>
              <n-button type="error" disabled>Delete My Account</n-button>
            </template>
            Are you sure you want to delete your account? This action is irreversible.
          </n-popconfirm>
        </n-space>
      </n-space>
    </n-card>

    <!-- Logout -->
    <n-button
      type="error"
      ghost
      @click="handleLogout"
      :block="isMobile"
    >
      Sign Out
    </n-button>
  </n-space>
</template>

<script setup lang="ts">
/**
 * User profile view component.
 *
 * Features:
 * - Display user information
 * - Show usage statistics
 * - Handle budget invitations
 * - Security settings (placeholder)
 * - Logout functionality
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NCard, NAvatar, NButton, NDescriptions, NDescriptionsItem,
  NGrid, NGi, NStatistic, NText, NDivider, NAlert, NPopconfirm,
  NTag, useMessage
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useBudgetStore } from '@/stores/budget'
import { invitationsAPI, type BudgetInvitationWithDetails } from '@/services/api'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()
const budgetStore = useBudgetStore()

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/** List of pending invitations */
const invitations = ref<BudgetInvitationWithDetails[]>([])

/** ID of invitation currently being processed */
const processingInvitation = ref<string | null>(null)

/**
 * Checks if the viewport is mobile-sized.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // Load budgets if not already loaded
  if (budgetStore.budgets.length === 0) {
    try {
      await budgetStore.fetchBudgets()
    } catch (error) {
      console.error('Error loading budgets:', error)
    }
  }

  // Load invitations
  try {
    invitations.value = await invitationsAPI.getMyInvitations()
  } catch (error) {
    console.error('Error loading invitations:', error)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/**
 * Formats a date string for display.
 * @param dateString - ISO date string
 */
const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
}

/** Number of transactions this month */
const transactionsThisMonth = computed(() => {
  const now = new Date()
  const thisMonth = now.getMonth()
  const thisYear = now.getFullYear()

  return budgetStore.transactions.filter(t => {
    const date = new Date(t.date)
    return date.getMonth() === thisMonth && date.getFullYear() === thisYear
  }).length
})

/** Total number of categories */
const totalCategories = computed(() => {
  return budgetStore.categories.length
})

/** Total number of recurring transactions */
const totalRecurring = computed(() => {
  return budgetStore.recurringTransactions.length
})

/**
 * Accepts a budget invitation.
 * @param id - Invitation ID
 */
const handleAcceptInvitation = async (id: string) => {
  processingInvitation.value = id
  try {
    await invitationsAPI.acceptInvitation(id)
    message.success('Invitation accepted!')
    invitations.value = invitations.value.filter(inv => inv.id !== id)
    // Reload budgets
    await budgetStore.fetchBudgets()
  } catch (error) {
    console.error('Error accepting invitation:', error)
    message.error('Error accepting invitation')
  } finally {
    processingInvitation.value = null
  }
}

/**
 * Rejects a budget invitation.
 * @param id - Invitation ID
 */
const handleRejectInvitation = async (id: string) => {
  processingInvitation.value = id
  try {
    await invitationsAPI.rejectInvitation(id)
    message.success('Invitation declined')
    invitations.value = invitations.value.filter(inv => inv.id !== id)
  } catch (error) {
    console.error('Error rejecting invitation:', error)
    message.error('Error declining invitation')
  } finally {
    processingInvitation.value = null
  }
}

/**
 * Logs out the current user.
 */
const handleLogout = () => {
  authStore.logout()
  message.info('Signed out successfully')
  router.push('/login')
}

/**
 * Handles account deletion (placeholder).
 */
const handleDeleteAccount = () => {
  message.error('Feature not implemented')
}
</script>