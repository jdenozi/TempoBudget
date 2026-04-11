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
  <n-config-provider :theme="darkTheme">
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
          <span class="version">{{ appVersion }}</span>
          <span v-if="!collapsed" class="date">{{ buildDate }}</span>
        </div>
      </n-layout-sider>

      <n-layout>
        <!-- Header with add transaction button -->
        <n-layout-header bordered style="height: 64px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 99; background: #18181c;">
          <div style="display: flex; align-items: center; gap: 16px;">
            <n-button
              v-if="isMobile"
              text
              @click="showDrawer = true"
              style="font-size: 20px;"
            >
              ☰
            </n-button>
            <div style="display: flex; align-items: center; gap: 12px;">
              <img src="@/assets/logo.png" alt="Tempo Finance" style="width: 36px; height: 36px; border-radius: 8px;" />
              <h2 v-if="!isMobile" style="margin: 0;">Tempo Finance</h2>
            </div>

            <div class="pro-toggle">
              <n-switch
                :value="proStore.isProMode"
                @update:value="handleProToggle"
                :round="false"
              >
                <template #checked>Pro</template>
                <template #unchecked>Pro</template>
              </n-switch>
            </div>
          </div>

          <n-button
            v-if="!proStore.isProMode"
            type="primary"
            circle
            @click="showTransactionDrawer = true"
            size="large"
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
        <n-drawer-content :title="t('common.filter')" closable body-content-style="display: flex; flex-direction: column; height: 100%;">
          <n-menu
            :options="menuOptions"
            v-model:value="activeKey"
            @update:value="handleMenuClickMobile"
            style="flex: 1;"
          />
          <div class="version-info">
            <span class="version">{{ appVersion }}</span>
            <span class="date">{{ buildDate }}</span>
          </div>
        </n-drawer-content>
      </n-drawer>

      <!-- Add Transaction Drawer -->
      <n-drawer
        v-model:show="showTransactionDrawer"
        :width="isMobile ? '100%' : 400"
        placement="right"
      >
        <n-drawer-content :title="t('transaction.addTransaction')" closable>
          <AddTransactionForm @success="handleTransactionSuccess" />
        </n-drawer-content>
      </n-drawer>
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
  NMenu, NButton, NDrawer, NDrawerContent, NMessageProvider, NSwitch,
  darkTheme, lightTheme
} from 'naive-ui'
import { ref, h, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  DashboardOutlined, HistoryOutlined, BarChartOutlined,
  UserOutlined, SettingOutlined, SyncOutlined, TeamOutlined,
  ShoppingOutlined, TagOutlined, GiftOutlined, SwapOutlined,
  FileTextOutlined, FileDoneOutlined, AppstoreOutlined, AuditOutlined
} from '@vicons/antd'
import type { MenuOption } from 'naive-ui'
import AddTransactionForm from './AddTransactionForm.vue'
import { useMobileDetect } from '@/composables/useMobileDetect'
import { useProStore } from '@/stores/pro'

const router = useRouter()
const { t } = useI18n()
const proStore = useProStore()

/** Whether the sidebar is collapsed */
const collapsed = ref(false)

/** Currently active menu item */
const activeKey = ref('dashboard')

/** Mobile menu drawer visibility */
const showDrawer = ref(false)

/** Transaction form drawer visibility */
const showTransactionDrawer = ref(false)

const { isMobile } = useMobileDetect()

onMounted(() => {
  proStore.initProMode()
  // Sync activeKey with current route
  const currentRoute = router.currentRoute.value.name as string
  if (currentRoute) activeKey.value = currentRoute
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
const personalMenuOptions = computed<MenuOption[]>(() => [
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
    label: t('nav.profile'),
    key: 'profile',
    icon: () => h(UserOutlined)
  }
])

/** Pro mode menu options */
const proMenuOptions = computed<MenuOption[]>(() => [
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
])

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
}

.version-info .date {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
}

.pro-toggle {
  margin-left: 8px;
}
</style>
