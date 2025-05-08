<!--
  Copyright (c) 2024 Tempo Budget
  SPDX-License-Identifier: MIT

  Root Application Component

  This is the root component that serves as the entry point for the Vue application.
  It renders the router view to display the appropriate page based on the current route.
-->

<template>
  <router-view />
</template>

<script setup lang="ts">
/**
 * Root application component.
 * Renders the current route's component through router-view.
 */
</script>

<style>
/* Global CSS Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Base body styles */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
</style>