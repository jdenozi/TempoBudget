/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Authentication Store
 *
 * Pinia store for managing user authentication state.
 * Handles login, registration, logout, and persistence of auth state in localStorage.
 *
 * State:
 * - user: Current authenticated user or null
 * - token: JWT token or null
 * - isAuthenticated: Boolean indicating authentication status
 *
 * Actions:
 * - init(): Restore auth state from localStorage on app startup
 * - register(): Create new user account and authenticate
 * - login(): Authenticate existing user
 * - logout(): Clear authentication state
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authAPI, type User } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  /** Currently authenticated user */
  const user = ref<User | null>(null)

  /** JWT authentication token */
  const token = ref<string | null>(null)

  /** Whether the user is currently authenticated */
  const isAuthenticated = ref(false)

  /**
   * Initializes authentication state from localStorage.
   * Called on application startup to restore previous session.
   */
  function init() {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('auth_user')

    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
      isAuthenticated.value = true
    }
  }

  /**
   * Registers a new user account.
   * On success, stores the token and user data in state and localStorage.
   *
   * @param email - User's email address
   * @param name - User's display name
   * @param password - User's password
   * @returns The authentication response
   */
  async function register(email: string, name: string, password: string) {
    const response = await authAPI.register(email, name, password)

    token.value = response.token
    user.value = response.user
    isAuthenticated.value = true

    localStorage.setItem('auth_token', response.token)
    localStorage.setItem('auth_user', JSON.stringify(response.user))

    return response
  }

  /**
   * Authenticates an existing user.
   * On success, stores the token and user data in state and localStorage.
   *
   * @param email - User's email address
   * @param password - User's password
   * @returns The authentication response
   */
  async function login(email: string, password: string) {
    const response = await authAPI.login(email, password)

    token.value = response.token
    user.value = response.user
    isAuthenticated.value = true

    localStorage.setItem('auth_token', response.token)
    localStorage.setItem('auth_user', JSON.stringify(response.user))

    return response
  }

  /**
   * Logs out the current user.
   * Clears all authentication state and removes data from localStorage.
   */
  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false

    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return {
    user,
    token,
    isAuthenticated,
    init,
    register,
    login,
    logout,
  }
})