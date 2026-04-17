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
    <h1 class="page-title">{{ t('profile.title') }}</h1>

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
        <n-flex align="center" :size="16">
          <div class="avatar-wrapper" @click="triggerAvatarUpload">
            <n-avatar
              :size="isMobile ? 80 : 100"
              round
              :src="avatarSrc || undefined"
            >
              <template v-if="!avatarSrc">{{ userInitials }}</template>
            </n-avatar>
            <div class="avatar-overlay">
              <n-icon :component="CameraOutline" :size="22" />
            </div>
            <n-spin v-if="uploadingAvatar" :size="20" class="avatar-spinner" />
          </div>
          <n-button size="small" :loading="uploadingAvatar" @click="triggerAvatarUpload">
            {{ t('profile.changePhoto') }}
          </n-button>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="file-input"
            @change="handleAvatarChange"
          />
        </n-flex>

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
    <n-card :title="t('profile.statistics')">
      <n-grid :cols="isMobile ? 2 : 4" :x-gap="12" :y-gap="12">
        <n-gi>
          <n-statistic :label="t('profile.activeBudgets')" :value="budgetStore.budgets.length" />
        </n-gi>
        <n-gi>
          <n-statistic :label="t('profile.transactionsThisMonth')" :value="transactionsThisMonth" />
        </n-gi>
        <n-gi>
          <n-statistic :label="t('profile.categories')" :value="totalCategories" />
        </n-gi>
        <n-gi>
          <n-statistic :label="t('profile.recurringCount')" :value="totalRecurring" />
        </n-gi>
      </n-grid>
    </n-card>

    <!-- Pending Budget Invitations -->
    <n-card :title="t('profile.pendingInvitations')" v-if="invitations.length > 0">
      <n-space vertical>
        <n-alert
          v-for="invitation in invitations"
          :key="invitation.id"
          type="info"
          closable
          @close="handleRejectInvitation(invitation.id)"
        >
          <template #header>
            {{ t('profile.invitationToBudget', { name: invitation.budget_name }) }}
          </template>

          <p class="invitation-body">
            {{ t('profile.inviterInvitesAs', { name: invitation.inviter_name }) }}
            <n-tag :type="invitation.role === 'owner' ? 'success' : 'default'" size="small">
              {{ invitation.role === 'owner' ? t('profile.roleOwner') : t('profile.roleMember') }}
            </n-tag>
          </p>

          <n-space>
            <n-button
              type="success"
              size="small"
              :loading="processingInvitation === invitation.id"
              @click="handleAcceptInvitation(invitation.id)"
            >
              {{ t('profile.accept') }}
            </n-button>
            <n-button
              size="small"
              :loading="processingInvitation === invitation.id"
              @click="handleRejectInvitation(invitation.id)"
            >
              {{ t('profile.decline') }}
            </n-button>
          </n-space>
        </n-alert>
      </n-space>
    </n-card>

    <!-- Pending Project Invitations -->
    <n-card :title="t('profile.projectInvitations')" v-if="projectInvitations.length > 0">
      <n-space vertical>
        <n-alert
          v-for="invitation in projectInvitations"
          :key="invitation.id"
          type="info"
          closable
          @close="handleRejectProjectInvitation(invitation.id)"
        >
          <template #header>
            {{ t('profile.projectInvitationTo', { name: invitation.project_name }) }}
          </template>

          <p class="invitation-body">
            {{ t('profile.projectInviterInvitesAs', { name: invitation.inviter_name }) }}
            <n-tag :type="invitation.role === 'owner' ? 'success' : 'default'" size="small">
              {{ invitation.role === 'owner' ? t('profile.roleOwner') : t('profile.roleMember') }}
            </n-tag>
          </p>

          <n-space>
            <n-button
              type="success"
              size="small"
              :loading="processingProjectInvitation === invitation.id"
              @click="handleAcceptProjectInvitation(invitation.id)"
            >
              {{ t('profile.accept') }}
            </n-button>
            <n-button
              size="small"
              :loading="processingProjectInvitation === invitation.id"
              @click="handleRejectProjectInvitation(invitation.id)"
            >
              {{ t('profile.decline') }}
            </n-button>
          </n-space>
        </n-alert>
      </n-space>
    </n-card>

    <!-- Settings -->
    <n-card :title="t('profile.settings')">
      <div class="settings-row">
        <n-flex align="center" :size="12">
          <n-icon :component="LanguageOutline" :size="20" class="settings-icon" />
          <div>
            <div class="settings-label">{{ t('profile.language') }}</div>
            <n-text depth="3">{{ t('profile.languageDesc') }}</n-text>
          </div>
        </n-flex>
        <n-select
          :value="locale"
          :options="languageOptions"
          class="settings-control"
          @update:value="handleLanguageChange"
        />
      </div>

      <n-divider />

      <div class="settings-row">
        <n-flex align="center" :size="12">
          <n-icon :component="TimeOutline" :size="20" class="settings-icon" />
          <div>
            <div class="settings-label">{{ t('profile.autoLogout') }}</div>
            <n-text depth="3">{{ t('profile.autoLogoutDesc') }}</n-text>
          </div>
        </n-flex>
        <n-select
          :value="settingsStore.inactivityTimeout"
          :options="inactivityOptions"
          class="settings-control"
          @update:value="settingsStore.setInactivityTimeout"
        />
      </div>

      <n-divider />

      <div class="settings-row">
        <n-flex align="center" :size="12">
          <n-icon :component="LockClosedOutline" :size="20" class="settings-icon" />
          <div>
            <div class="settings-label">{{ t('profile.password') }}</div>
            <n-text depth="3">{{ t('profile.passwordDesc') }}</n-text>
          </div>
        </n-flex>
        <n-button size="small" @click="showChangePassword = true">
          {{ t('profile.changePassword') }}
        </n-button>
      </div>

      <n-divider />

      <div class="settings-row">
        <n-flex align="center" :size="12">
          <n-icon :component="ShieldCheckmarkOutline" :size="20" class="settings-icon" />
          <div>
            <div class="settings-label">{{ t('profile.twoFactor') }}</div>
            <n-text depth="3">{{ t('profile.twoFactorDesc') }}</n-text>
          </div>
        </n-flex>
        <n-button size="small" disabled>{{ t('profile.enable') }}</n-button>
      </div>
    </n-card>

    <!-- Danger Zone -->
    <n-card :title="t('profile.dangerZone')" class="danger-zone">
      <n-space vertical>
        <n-alert type="warning" :title="t('profile.dangerZoneWarning')">
          {{ t('profile.dangerZoneDesc') }}
        </n-alert>

        <n-space :vertical="isMobile">
          <n-button disabled>{{ t('profile.exportData') }}</n-button>

          <n-popconfirm @positive-click="handleDeleteAccount">
            <template #trigger>
              <n-button type="error" disabled>{{ t('profile.deleteAccount') }}</n-button>
            </template>
            {{ t('profile.deleteAccountConfirm') }}
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
      <template #icon>
        <n-icon :component="LogOutOutline" />
      </template>
      {{ t('profile.signOut') }}
    </n-button>

    <!-- Change Password Modal -->
    <n-modal v-model:show="showChangePassword">
      <n-card
        :title="t('profile.changePassword')"
        :bordered="false"
        size="huge"
        class="password-modal"
      >
        <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules">
          <n-form-item :label="t('profile.currentPassword')" path="currentPassword">
            <n-input
              v-model:value="passwordForm.currentPassword"
              type="password"
              show-password-on="click"
              :placeholder="t('profile.currentPasswordPlaceholder')"
            />
          </n-form-item>

          <n-form-item :label="t('profile.newPassword')" path="newPassword">
            <n-input
              v-model:value="passwordForm.newPassword"
              type="password"
              show-password-on="click"
              :placeholder="t('profile.newPasswordPlaceholder')"
            />
          </n-form-item>

          <n-form-item :label="t('profile.confirmNewPassword')" path="confirmPassword">
            <n-input
              v-model:value="passwordForm.confirmPassword"
              type="password"
              show-password-on="click"
              :placeholder="t('profile.confirmPasswordPlaceholder')"
            />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showChangePassword = false">{{ t('common.cancel') }}</n-button>
            <n-button
              type="primary"
              :loading="changingPassword"
              @click="handleChangePassword"
            >
              {{ t('profile.changePassword') }}
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
  NSpace, NFlex, NCard, NAvatar, NButton, NDescriptions, NDescriptionsItem,
  NGrid, NGi, NStatistic, NText, NDivider, NAlert, NPopconfirm,
  NTag, NModal, NForm, NFormItem, NInput, NSelect, NSpin, NIcon, useMessage,
  type FormInst, type FormRules
} from 'naive-ui'
import {
  CameraOutline, LanguageOutline, TimeOutline, LockClosedOutline,
  ShieldCheckmarkOutline, LogOutOutline,
} from '@vicons/ionicons5'
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
    message.error(t('profile.avatarTooLarge'))
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

const passwordRules = computed<FormRules>(() => ({
  currentPassword: [
    { required: true, message: t('profile.currentPasswordRequired') }
  ],
  newPassword: [
    { required: true, message: t('profile.newPasswordRequired') },
    { min: 6, message: t('profile.passwordMinLength') }
  ],
  confirmPassword: [
    { required: true, message: t('profile.confirmPasswordRequired') },
    {
      validator: (_rule, value) => {
        return value === passwordForm.value.newPassword
      },
      message: t('profile.passwordsDoNotMatch')
    }
  ]
}))

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
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
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

const avatarSrc = computed(() => {
  const user = authStore.user
  if (!user?.avatar) return ''
  const separator = user.avatar.includes('?') ? '&' : '?'
  return `${user.avatar}${separator}v=${encodeURIComponent(user.updated_at || '')}`
})

const userInitials = computed(() => {
  const name = authStore.user?.name || authStore.user?.email || '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
})

const handleAcceptInvitation = async (id: string) => {
  processingInvitation.value = id
  try {
    await invitationsAPI.acceptInvitation(id)
    message.success(t('profile.invitationAccepted'))
    invitations.value = invitations.value.filter(inv => inv.id !== id)
    await budgetStore.fetchBudgets()
  } catch (error) {
    console.error('Error accepting invitation:', error)
    message.error(t('profile.invitationAcceptError'))
  } finally {
    processingInvitation.value = null
  }
}

const handleRejectInvitation = async (id: string) => {
  processingInvitation.value = id
  try {
    await invitationsAPI.rejectInvitation(id)
    message.success(t('profile.invitationDeclined'))
    invitations.value = invitations.value.filter(inv => inv.id !== id)
  } catch (error) {
    console.error('Error rejecting invitation:', error)
    message.error(t('profile.invitationDeclineError'))
  } finally {
    processingInvitation.value = null
  }
}

const handleAcceptProjectInvitation = async (id: string) => {
  processingProjectInvitation.value = id
  try {
    await projectStore.acceptProjectInvitation(id)
    message.success(t('profile.invitationAccepted'))
    await projectStore.fetchProjects()
  } catch (error) {
    console.error('Error accepting project invitation:', error)
    message.error(t('profile.invitationAcceptError'))
  } finally {
    processingProjectInvitation.value = null
  }
}

const handleRejectProjectInvitation = async (id: string) => {
  processingProjectInvitation.value = id
  try {
    await projectStore.rejectProjectInvitation(id)
    message.success(t('profile.invitationDeclined'))
  } catch (error) {
    console.error('Error rejecting project invitation:', error)
    message.error(t('profile.invitationDeclineError'))
  } finally {
    processingProjectInvitation.value = null
  }
}

const handleLogout = () => {
  authStore.logout()
  message.info(t('auth.logoutSuccess'))
  router.push('/login')
}

const handleDeleteAccount = () => {
  message.error(t('profile.featureNotImplemented'))
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
    message.success(t('profile.passwordChanged'))
    showChangePassword.value = false
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    }
  } catch (error: any) {
    console.error('Error changing password:', error)
    if (error.response?.status === 400) {
      message.error(t('profile.currentPasswordIncorrect'))
    } else {
      message.error(t('profile.passwordChangeError'))
    }
  } finally {
    changingPassword.value = false
  }
}
</script>

<style scoped>
.page-title {
  margin: 0;
  font-size: clamp(20px, 5vw, 28px);
}
.avatar-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
  line-height: 0;
}
.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  opacity: 0;
  transition: opacity 0.18s ease;
  pointer-events: none;
  border-radius: 50%;
}
.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}
.avatar-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.file-input {
  display: none;
}
.settings-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 0;
}
.settings-icon {
  color: var(--n-text-color-3, rgba(255, 255, 255, 0.5));
}
.settings-label {
  font-weight: 500;
}
.settings-control {
  width: 180px;
  max-width: 100%;
}
.invitation-body {
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.password-modal {
  width: 420px;
  max-width: 95vw;
}
.danger-zone :deep(.n-card-header) {
  color: var(--color-error, #ef4444);
}
</style>
