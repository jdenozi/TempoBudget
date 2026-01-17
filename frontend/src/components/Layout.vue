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
            <h2 style="margin: 0;">Tempo Budget</h2>
          </div>

          <n-button
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
        <n-drawer-content title="Menu" closable body-content-style="display: flex; flex-direction: column; height: 100%;">
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
        <n-drawer-content title="New Transaction" closable>
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
  NMenu, NButton, NDrawer, NDrawerContent, NMessageProvider, darkTheme, lightTheme
} from 'naive-ui'
import { ref, h, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  DashboardOutlined, HistoryOutlined, BarChartOutlined,
  UserOutlined, SettingOutlined, SyncOutlined
} from '@vicons/antd'
import type { MenuOption } from 'naive-ui'
import AddTransactionForm from './AddTransactionForm.vue'

const router = useRouter()

/** Whether the sidebar is collapsed */
const collapsed = ref(false)

/** Currently active menu item */
const activeKey = ref('dashboard')

/** Mobile menu drawer visibility */
const showDrawer = ref(false)

/** Transaction form drawer visibility */
const showTransactionDrawer = ref(false)

/** Whether the viewport is mobile-sized */
const isMobile = ref(false)

/**
 * Checks if the viewport is mobile-sized and updates state.
 */
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

/** Navigation menu options */
const menuOptions: MenuOption[] = [
  {
    label: 'My Budgets',
    key: 'dashboard',
    icon: () => h(DashboardOutlined)
  },
  {
    label: 'Recurring',
    key: 'recurring',
    icon: () => h(SyncOutlined)
  },
  {
    label: 'History',
    key: 'history',
    icon: () => h(HistoryOutlined)
  },
  {
    label: 'Charts',
    key: 'charts',
    icon: () => h(BarChartOutlined)
  },
  {
    label: 'Profile',
    key: 'profile',
    icon: () => h(UserOutlined)
  }
]

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

</style>
