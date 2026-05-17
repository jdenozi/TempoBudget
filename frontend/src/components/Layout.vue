<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Main Layout Component

  Provides the application shell with responsive navigation:
  - Desktop: Collapsible sidebar with menu
  - Mobile: Drawer-based navigation
  - Header with transaction quick-add button
  - Transaction drawer for adding new transactions
-->

<template>
  <n-message-provider>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-layout has-sider style="height: 100vh">
      <!-- Desktop Sidebar -->
      <n-layout-sider
        v-if="!isMobile"
        bordered
        collapse-mode="width"
        :collapsed-width="64"
        :width="240"
        show-trigger
        @collapse="collapsed = true"
        @expand="collapsed = false"
        content-style="display: flex; flex-direction: column; height: 100%;"
      >
        <n-menu
          :collapsed="collapsed"
          :collapsed-width="64"
          :collapsed-icon-size="22"
          :options="menuOptions"
          v-model:value="activeKey"
          @update:value="handleMenuClick"
          style="flex: 1;"
        />
        <div class="version-info" :class="{ collapsed }">
          <button type="button" class="version" @click="showReleaseNotes = true" :title="t('common.releaseNotes')">
            {{ appVersion }}
          </button>
          <span v-if="!collapsed" class="date">{{ buildDate }}</span>
        </div>
      </n-layout-sider>

      <n-layout>
        <!-- Header with add transaction button -->
        <n-layout-header bordered class="app-header">
          <n-flex align="center" :size="16">
            <n-button
              v-if="isMobile"
              text
              @click="showDrawer = true"
              class="mobile-menu-btn"
              :aria-label="t('nav.menu')"
            >
              ☰
            </n-button>
            <n-flex align="center" :size="12">
              <img src="@/assets/logo.png" alt="Tempo Finance" class="app-logo" />
              <h2 v-if="!isMobile" class="app-title">Tempo Finance</h2>
            </n-flex>

            <div class="pro-toggle">
              <n-switch
                v-if="subscriptionStore.hasProAccess"
                :value="proStore.isProMode"
                @update:value="handleProToggle"
                :round="false"
              >
                <template #checked>Pro</template>
                <template #unchecked>Pro</template>
              </n-switch>
              <n-button
                v-else
                text
                type="primary"
                size="small"
                @click="router.push('/pricing')"
              >
                {{ t('subscription.upgradeToPro') }}
              </n-button>
            </div>
          </n-flex>

          <n-button
            type="primary"
            circle
            @click="handleAddClick"
            size="large"
            :aria-label="t('nav.addTransaction')"
            :title="t('nav.addTransaction')"
          >
            +
          </n-button>
        </n-layout-header>

        <n-layout-content content-style="padding: 16px;">
          <router-view />
        </n-layout-content>
      </n-layout>

      <!-- Mobile Menu Drawer -->
      <n-drawer v-model:show="showDrawer" :width="280" placement="left">
        <n-drawer-content :title="t('nav.menu')" closable body-content-style="display: flex; flex-direction: column; height: 100%;">
          <n-menu
            :options="menuOptions"
            v-model:value="activeKey"
            @update:value="handleMenuClickMobile"
            style="flex: 1;"
          />
          <div class="version-info">
            <button type="button" class="version" @click="showReleaseNotes = true" :title="t('common.releaseNotes')">
              {{ appVersion }}
            </button>
            <span class="date">{{ buildDate }}</span>
          </div>
        </n-drawer-content>
      </n-drawer>

      <!-- Add Transaction Drawer (Personal) -->
      <n-drawer
        v-model:show="showTransactionDrawer"
        :width="isMobile ? '100%' : 400"
        placement="right"
      >
        <n-drawer-content :title="t('transaction.addTransaction')" closable>
          <AddTransactionForm @success="handleTransactionSuccess" />
        </n-drawer-content>
      </n-drawer>

      <!-- Add Transaction Drawer (Pro) -->
      <n-drawer
        v-model:show="showProTransactionDrawer"
        :width="isMobile ? '100%' : 480"
        placement="right"
      >
        <n-drawer-content :title="t('pro.transactions.addTransaction')" closable>
          <ProTransactionForm @success="handleProTransactionSuccess" />
        </n-drawer-content>
      </n-drawer>

      <!-- Release Notes Modal -->
      <ReleaseNotesModal v-model:show="showReleaseNotes" />

      <!-- Help Chat -->
      <HelpChat />
    </n-layout>
  </n-config-provider>
    </n-message-provider>
</template>

<script setup lang="ts">
/**
 * Main layout component providing the application shell.
 *
 * Features:
 * - Responsive sidebar (desktop) / drawer (mobile) navigation
 * - Dark theme configuration
 * - Quick-add transaction button in header
 * - Menu navigation to all main views
 */

import {
  NConfigProvider, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent,
  NMenu, NButton, NFlex, NDrawer, NDrawerContent, NMessageProvider, NSwitch,
  darkTheme, lightTheme
} from 'naive-ui'
import { ref, h, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  DashboardOutlined, HistoryOutlined, BarChartOutlined,
  UserOutlined, SettingOutlined, SyncOutlined, TeamOutlined,
  ShoppingOutlined, TagOutlined, GiftOutlined, SwapOutlined,
  FileTextOutlined, FileDoneOutlined, AppstoreOutlined, AuditOutlined,
  ProjectOutlined, ToolOutlined
} from '@vicons/antd'
import type { MenuOption } from 'naive-ui'
import AddTransactionForm from './AddTransactionForm.vue'
import ProTransactionForm from './pro/ProTransactionForm.vue'
import ReleaseNotesModal from './modals/ReleaseNotesModal.vue'
import HelpChat from './HelpChat.vue'
import { themeOverrides } from '@/theme'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { useProStore } from '@/stores/pro'
import { useAuthStore } from '@/stores/auth'
import { useSubscriptionStore } from '@/stores/subscription'

const router = useRouter()
const { t } = useI18n()
const proStore = useProStore()
const authStore = useAuthStore()
const subscriptionStore = useSubscriptionStore()

/** Whether the sidebar is collapsed */
const collapsed = ref(false)

/** Currently active menu item */
const activeKey = ref('dashboard')

/** Mobile menu drawer visibility */
const showDrawer = ref(false)

/** Personal transaction form drawer visibility */
const showTransactionDrawer = ref(false)
/** Pro transaction form drawer visibility */
const showProTransactionDrawer = ref(false)
const showReleaseNotes = ref(false)

/** Open the right drawer based on current mode */
const handleAddClick = () => {
  if (proStore.isProMode) {
    showProTransactionDrawer.value = true
  } else {
    showTransactionDrawer.value = true
  }
}

const { isMobile } = useMobileDetect()

onMounted(async () => {
  proStore.initProMode()
  // Sync activeKey with current route
  const currentRoute = router.currentRoute.value.name as string
  if (currentRoute) activeKey.value = currentRoute
  // Fetch pro access status
  await subscriptionStore.fetchProAccess()
})

/** Handle pro mode toggle */
const handleProToggle = (value: boolean) => {
  proStore.setProMode(value)
  if (value) {
    activeKey.value = 'pro-dashboard'
    router.push({ name: 'pro-dashboard' })
  } else {
    activeKey.value = 'dashboard'
    router.push({ name: 'dashboard' })
  }
}

/** Personal mode menu options */
const personalMenuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      label: t('nav.dashboard'),
      key: 'dashboard',
      icon: () => h(DashboardOutlined)
    },
    {
      label: t('nav.recurring'),
      key: 'recurring',
      icon: () => h(SyncOutlined)
    },
    {
      label: t('nav.history'),
      key: 'history',
      icon: () => h(HistoryOutlined)
    },
    {
      label: t('nav.charts'),
      key: 'charts',
      icon: () => h(BarChartOutlined)
    },
    {
      label: t('nav.loans'),
      key: 'loans',
      icon: () => h(SwapOutlined)
    },
    {
      label: t('nav.projects'),
      key: 'projects',
      icon: () => h(ProjectOutlined)
    },
    {
      label: t('nav.profile'),
      key: 'profile',
      icon: () => h(UserOutlined)
    }
  ]

  // Add admin menu if user is admin
  if (authStore.user?.is_admin) {
    options.push({
      label: t('nav.admin'),
      key: 'admin-dashboard',
      icon: () => h(ToolOutlined)
    })
  }

  return options
})

/** Pro mode menu options */
const proMenuOptions = computed<MenuOption[]>(() => {
  const options: MenuOption[] = [
    {
      label: t('nav.proDashboard'),
      key: 'pro-dashboard',
      icon: () => h(DashboardOutlined)
    },
    {
      label: t('nav.proClients'),
      key: 'pro-clients',
      icon: () => h(TeamOutlined)
    },
    {
      label: t('nav.proProducts'),
      key: 'pro-products',
      icon: () => h(ShoppingOutlined)
    },
    {
      label: t('nav.proInvoices'),
      key: 'pro-invoices',
      icon: () => h(FileTextOutlined)
    },
    {
      label: t('nav.proQuotes'),
      key: 'pro-quotes',
      icon: () => h(FileDoneOutlined)
    },
    {
      label: t('nav.proCategories'),
      key: 'pro-categories',
      icon: () => h(AppstoreOutlined)
    },
    {
      label: t('nav.proDeclaration'),
      key: 'pro-declaration',
      icon: () => h(AuditOutlined)
    },
    {
      label: t('nav.proCoupons'),
      key: 'pro-coupons',
      icon: () => h(TagOutlined)
    },
    {
      label: t('nav.proGiftCards'),
      key: 'pro-gift-cards',
      icon: () => h(GiftOutlined)
    },
    {
      label: t('nav.projects'),
      key: 'projects',
      icon: () => h(ProjectOutlined)
    },
    {
      label: t('nav.proRecurring'),
      key: 'pro-recurring',
      icon: () => h(SyncOutlined)
    },
    {
      label: t('nav.proHistory'),
      key: 'pro-history',
      icon: () => h(HistoryOutlined)
    },
    {
      label: t('nav.proCharts'),
      key: 'pro-charts',
      icon: () => h(BarChartOutlined)
    },
    {
      label: t('nav.profile'),
      key: 'profile',
      icon: () => h(UserOutlined)
    }
  ]

  // Add admin menu if user is admin
  if (authStore.user?.is_admin) {
    options.push({
      label: t('nav.admin'),
      key: 'admin-dashboard',
      icon: () => h(ToolOutlined)
    })
  }

  return options
})

/** Navigation menu options (switches based on pro mode) */
const menuOptions = computed<MenuOption[]>(() =>
  proStore.isProMode ? proMenuOptions.value : personalMenuOptions.value
)

/**
 * Handles menu item click on desktop.
 * @param key - The menu item key (route name)
 */
const handleMenuClick = (key: string) => {
  activeKey.value = key
  router.push({ name: key })
}

/**
 * Handles menu item click on mobile.
 * Closes the drawer after navigation.
 * @param key - The menu item key (route name)
 */
const handleMenuClickMobile = (key: string) => {
  activeKey.value = key
  router.push({ name: key })
  showDrawer.value = false
}

/**
 * Handles successful transaction creation.
 * Closes the transaction drawer.
 */
const handleTransactionSuccess = () => {
  showTransactionDrawer.value = false
}

const handleProTransactionSuccess = () => {
  showProTransactionDrawer.value = false
}

declare const __APP_VERSION__: string
declare const __BUILD_DATE__: string
const appVersion = __APP_VERSION__
const buildDate = __BUILD_DATE__
</script>

<style scoped>
.version-info {
  padding: 12px 16px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  font-family: monospace;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.version-info.collapsed {
  padding: 12px 8px;
  align-items: center;
}

.version-info .version {
  font-weight: 500;
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  font: inherit;
  cursor: pointer;
  text-align: left;
  transition: color 0.15s ease;
}

.version-info .version:hover {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: underline;
}

.version-info .date {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
}

.pro-toggle {
  margin-left: 8px;
}

.mobile-menu-btn {
  font-size: 20px;
}
.app-logo {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}
.app-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  background: linear-gradient(180deg, #f3f4f6 0%, #d1d5db 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.app-header {
  height: 64px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 99;
  background: linear-gradient(180deg, rgba(24, 26, 32, 0.92), rgba(18, 20, 25, 0.78));
  backdrop-filter: saturate(140%) blur(10px);
  -webkit-backdrop-filter: saturate(140%) blur(10px);
}
</style>
