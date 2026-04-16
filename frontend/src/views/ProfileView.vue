<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Profile View

  User profile management page displaying:
  - Editable personal information (name, phone)
  - Avatar upload
  - Usage statistics
  - Pending budget invitations
  - Security settings
  - Account actions (logout, delete)
-->

<template>
  <n-space vertical size="large">
    <h1 style="margin: 0; font-size: clamp(20px, 5vw, 28px);">{{ t('profile.title') }}</h1>

    <!-- User Information -->
    <n-card :title="t('profile.personalInfo')">
      <template #header-extra>
        <n-button
          v-if="!editing"
          size="small"
          @click="startEditing"
        >
          {{ t('profile.editProfile') }}
        </n-button>
        <n-space v-else>
          <n-button size="small" @click="cancelEditing">{{ t('common.cancel') }}</n-button>
          <n-button size="small" type="primary" :loading="savingProfile" @click="saveProfile">
            {{ t('common.save') }}
          </n-button>
        </n-space>
      </template>

      <n-space vertical size="large">
        <!-- Avatar -->
        <div style="display: flex; align-items: center; gap: 16px;">
          <div style="position: relative; cursor: pointer;" @click="triggerAvatarUpload">
            <n-avatar
              :size="isMobile ? 80 : 100"
              round
              :src="authStore.user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${authStore.user?.name}`"
            />
            <n-spin v-if="uploadingAvatar" :size="20" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);" />
          </div>
          <n-button size="small" :loading="uploadingAvatar" @click="triggerAvatarUpload">
            {{ t('profile.changePhoto') }}
          </n-button>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            style="display: none;"
            @change="handleAvatarChange"
          />
        </div>

        <!-- User Details -->
        <n-descriptions v-if="!editing" :column="1" bordered>
          <n-descriptions-item :label="t('profile.name')">
            {{ authStore.user?.name }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('profile.email')">
            {{ authStore.user?.email }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('profile.phone')">
            {{ authStore.user?.phone || '—' }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('profile.memberSince')">
            {{ formatDate(authStore.user?.created_at) }}
          </n-descriptions-item>
        </n-descriptions>

        <!-- Edit Mode -->
        <n-form v-else>
          <n-form-item :label="t('profile.name')">
            <n-input v-model:value="editForm.name" :placeholder="t('profile.name')" />
          </n-form-item>
          <n-form-item :label="t('profile.email')">
            <n-input :value="authStore.user?.email" disabled />
          </n-form-item>
          <n-form-item :label="t('profile.phone')">
            <n-input v-model:value="editForm.phone" :placeholder="t('profile.phone')" />
          </n-form-item>
        </n-form>
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

    <!-- Pending Project Invitations -->
    <n-card title="Invitations projet" v-if="projectInvitations.length > 0">
      <n-space vertical>
        <n-alert
          v-for="invitation in projectInvitations"
          :key="invitation.id"
          type="info"
          closable
          @close="handleRejectProjectInvitation(invitation.id)"
        >
          <template #header>
            Invitation au projet "{{ invitation.project_name }}"
          </template>

          <div style="margin-bottom: 12px;">
            <strong>{{ invitation.inviter_name }}</strong> vous invite à rejoindre ce projet en tant que
            <n-tag :type="invitation.role === 'owner' ? 'success' : 'default'" size="small">
              {{ invitation.role === 'owner' ? 'Propriétaire' : 'Membre' }}
            </n-tag>
          </div>

          <n-space>
            <n-button
              type="success"
              size="small"
              :loading="processingProjectInvitation === invitation.id"
              @click="handleAcceptProjectInvitation(invitation.id)"
            >
              Accepter
            </n-button>
            <n-button
              size="small"
              :loading="processingProjectInvitation === invitation.id"
              @click="handleRejectProjectInvitation(invitation.id)"
            >
              Refuser
            </n-button>
          </n-space>
        </n-alert>
      </n-space>
    </n-card>

    <!-- Settings -->
    <n-card :title="t('profile.title')">
      <n-space vertical>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-weight: 500;">{{ t('profile.language') }}</div>
            <n-text depth="3">{{ t('common.filter') }}</n-text>
          </div>
          <n-select
            :value="locale"
            :options="languageOptions"
            style="width: 150px;"
            @update:value="handleLanguageChange"
          />
        </div>

        <n-divider />

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-weight: 500;">Auto Logout</div>
            <n-text depth="3">Automatically log out after inactivity</n-text>
          </div>
          <n-select
            :value="settingsStore.inactivityTimeout"
            :options="inactivityOptions"
            style="width: 150px;"
            @update:value="settingsStore.setInactivityTimeout"
          />
        </div>

        <n-divider />

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <div style="font-weight: 500;">Password</div>
            <n-text depth="3">Manage your password</n-text>
          </div>
          <n-button size="small" @click="showChangePassword = true">Change Password</n-button>
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

    <!-- Change Password Modal -->
    <n-modal v-model:show="showChangePassword">
      <n-card
        title="Change Password"
        :bordered="false"
        size="huge"
        style="width: 400px; max-width: 95vw;"
      >
        <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules">
          <n-form-item label="Current Password" path="currentPassword">
            <n-input
              v-model:value="passwordForm.currentPassword"
              type="password"
              show-password-on="click"
              placeholder="Enter your current password"
            />
          </n-form-item>

          <n-form-item label="New Password" path="newPassword">
            <n-input
              v-model:value="passwordForm.newPassword"
              type="password"
              show-password-on="click"
              placeholder="Enter your new password"
            />
          </n-form-item>

          <n-form-item label="Confirm New Password" path="confirmPassword">
            <n-input
              v-model:value="passwordForm.confirmPassword"
              type="password"
              show-password-on="click"
              placeholder="Confirm your new password"
            />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showChangePassword = false">Cancel</n-button>
            <n-button
              type="primary"
              :loading="changingPassword"
              @click="handleChangePassword"
            >
              Change Password
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </n-space>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NCard, NAvatar, NButton, NDescriptions, NDescriptionsItem,
  NGrid, NGi, NStatistic, NText, NDivider, NAlert, NPopconfirm,
  NTag, NModal, NForm, NFormItem, NInput, NSelect, NSpin, useMessage,
  type FormInst, type FormRules
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useBudgetStore } from '@/stores/budget'
import { useSettingsStore, INACTIVITY_OPTIONS } from '@/stores/settings'
import { useProjectStore } from '@/stores/project'
import { authAPI, invitationsAPI, type BudgetInvitationWithDetails } from '@/services/api'
import { SUPPORTED_LOCALES, saveLocale, type Locale } from '@/i18n'

const router = useRouter()
const message = useMessage()
const { locale, t } = useI18n()
const authStore = useAuthStore()
const budgetStore = useBudgetStore()
const projectStore = useProjectStore()
const settingsStore = useSettingsStore()

const languageOptions = SUPPORTED_LOCALES.map(l => ({
  label: l.name,
  value: l.code,
}))

const handleLanguageChange = (newLocale: Locale) => {
  locale.value = newLocale
  saveLocale(newLocale)
  message.success(t('common.success'))
}

const inactivityOptions = INACTIVITY_OPTIONS.map(opt => ({
  label: opt.label,
  value: opt.value,
}))

const isMobile = ref(false)
const invitations = ref<BudgetInvitationWithDetails[]>([])
const processingInvitation = ref<string | null>(null)
const projectInvitations = computed(() => projectStore.projectInvitations)
const processingProjectInvitation = ref<string | null>(null)
const showChangePassword = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref<FormInst | null>(null)

/** Profile editing state */
const editing = ref(false)
const savingProfile = ref(false)
const uploadingAvatar = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const editForm = ref({ name: '', phone: '' })

const startEditing = () => {
  editForm.value = {
    name: authStore.user?.name || '',
    phone: authStore.user?.phone || '',
  }
  editing.value = true
}

const cancelEditing = () => {
  editing.value = false
}

const saveProfile = async () => {
  savingProfile.value = true
  try {
    await authStore.updateProfile({
      name: editForm.value.name || undefined,
      phone: editForm.value.phone || undefined,
    })
    message.success(t('profile.profileUpdated'))
    editing.value = false
  } catch (error) {
    console.error('Error updating profile:', error)
    message.error(t('errors.generic'))
  } finally {
    savingProfile.value = false
  }
}

const triggerAvatarUpload = () => {
  fileInputRef.value?.click()
}

const handleAvatarChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    message.error('File too large (max 2 MB)')
    return
  }

  uploadingAvatar.value = true
  try {
    await authStore.uploadAvatar(file)
    message.success(t('profile.avatarUpdated'))
  } catch (error) {
    console.error('Error uploading avatar:', error)
    message.error(t('errors.generic'))
  } finally {
    uploadingAvatar.value = false
    input.value = ''
  }
}

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules: FormRules = {
  currentPassword: [
    { required: true, message: 'Current password is required' }
  ],
  newPassword: [
    { required: true, message: 'New password is required' },
    { min: 6, message: 'Password must be at least 6 characters' }
  ],
  confirmPassword: [
    { required: true, message: 'Please confirm your new password' },
    {
      validator: (_rule, value) => {
        return value === passwordForm.value.newPassword
      },
      message: 'Passwords do not match'
    }
  ]
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  if (budgetStore.budgets.length === 0) {
    try {
      await budgetStore.fetchBudgets()
    } catch (error) {
      console.error('Error loading budgets:', error)
    }
  }

  try {
    invitations.value = await invitationsAPI.getMyInvitations()
  } catch (error) {
    console.error('Error loading invitations:', error)
  }

  try {
    await projectStore.fetchProjectInvitations()
  } catch (error) {
    console.error('Error loading project invitations:', error)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
}

const transactionsThisMonth = computed(() => {
  const now = new Date()
  const thisMonth = now.getMonth()
  const thisYear = now.getFullYear()

  return budgetStore.transactions.filter(t => {
    const date = new Date(t.date)
    return date.getMonth() === thisMonth && date.getFullYear() === thisYear
  }).length
})

const totalCategories = computed(() => budgetStore.categories.length)
const totalRecurring = computed(() => budgetStore.recurringTransactions.length)

const handleAcceptInvitation = async (id: string) => {
  processingInvitation.value = id
  try {
    await invitationsAPI.acceptInvitation(id)
    message.success('Invitation accepted!')
    invitations.value = invitations.value.filter(inv => inv.id !== id)
    await budgetStore.fetchBudgets()
  } catch (error) {
    console.error('Error accepting invitation:', error)
    message.error('Error accepting invitation')
  } finally {
    processingInvitation.value = null
  }
}

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

const handleAcceptProjectInvitation = async (id: string) => {
  processingProjectInvitation.value = id
  try {
    await projectStore.acceptProjectInvitation(id)
    message.success('Invitation acceptée !')
    await projectStore.fetchProjects()
  } catch (error) {
    console.error('Error accepting project invitation:', error)
    message.error('Erreur lors de l\'acceptation')
  } finally {
    processingProjectInvitation.value = null
  }
}

const handleRejectProjectInvitation = async (id: string) => {
  processingProjectInvitation.value = id
  try {
    await projectStore.rejectProjectInvitation(id)
    message.success('Invitation refusée')
  } catch (error) {
    console.error('Error rejecting project invitation:', error)
    message.error('Erreur')
  } finally {
    processingProjectInvitation.value = null
  }
}

const handleLogout = () => {
  authStore.logout()
  message.info('Signed out successfully')
  router.push('/login')
}

const handleDeleteAccount = () => {
  message.error('Feature not implemented')
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value?.validate()
  } catch {
    return
  }

  changingPassword.value = true
  try {
    await authAPI.changePassword(
      passwordForm.value.currentPassword,
      passwordForm.value.newPassword
    )
    message.success('Password changed successfully')
    showChangePassword.value = false
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    }
  } catch (error: any) {
    console.error('Error changing password:', error)
    if (error.response?.status === 400) {
      message.error('Current password is incorrect')
    } else {
      message.error('Error changing password')
    }
  } finally {
    changingPassword.value = false
  }
}
</script>
