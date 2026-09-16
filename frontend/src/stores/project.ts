/**
 * Copyright (c) 2024 Tempo Budget
 * SPDX-License-Identifier: MIT
 *
 * Project Store
 *
 * Pinia store for managing project budget state and operations.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  projectsAPI,
  type Project, type ProjectSummary, type ProjectPlannedExpense,
  type ProjectReminder, type ProjectTransaction, type ProjectCategoryWithSpent,
  type ProjectMemberWithUser, type ProjectInvitationWithDetails,
  type ProjectMemberBalance,
} from '@/services/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const summaries = ref<ProjectSummary[]>([])
  const currentProject = ref<Project | null>(null)
  const plannedExpenses = ref<ProjectPlannedExpense[]>([])
  const projectTransactions = ref<ProjectTransaction[]>([])
  const reminders = ref<ProjectReminder[]>([])
  const loading = ref(false)

  // ── Projects ──

  async function fetchProjects(params?: { status?: string; mode?: string }) {
    loading.value = true
    try {
      projects.value = await projectsAPI.getAll(params)
    } finally {
      loading.value = false
    }
  }

  async function fetchSummaries() {
    loading.value = true
    try {
      summaries.value = await projectsAPI.getSummaries()
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: string) {
    loading.value = true
    try {
      currentProject.value = await projectsAPI.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: { name: string; description?: string; target_date?: string; total_budget: number; mode: 'personal' | 'pro' }) {
    const project = await projectsAPI.create(data)
    projects.value.unshift(project)
    return project
  }

  async function updateProject(id: string, data: { name?: string; description?: string; target_date?: string; total_budget?: number; status?: string }) {
    const updated = await projectsAPI.update(id, data)
    const idx = projects.value.findIndex(p => p.id === id)
    if (idx !== -1) projects.value[idx] = updated
    if (currentProject.value?.id === id) currentProject.value = updated
    return updated
  }

  async function deleteProject(id: string) {
    await projectsAPI.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    if (currentProject.value?.id === id) currentProject.value = null
  }

  // ── Categories ──

  async function createCategory(projectId: string, data: { name: string; planned_amount: number }) {
    const category = await projectsAPI.createCategory(projectId, data)
    const newCat: ProjectCategoryWithSpent = {
      id: category.id,
      project_id: category.project_id,
      name: category.name,
      planned_amount: category.planned_amount,
      created_at: category.created_at,
      total_spent: 0,
      remaining: category.planned_amount,
    }

    // Update in currentProject
    if (currentProject.value?.id === projectId) {
      currentProject.value.categories.push(newCat)
    }

    // Also update in projects list
    const projectInList = projects.value.find(p => p.id === projectId)
    if (projectInList) {
      projectInList.categories.push({ ...newCat })
    }

    return category
  }

  async function updateCategory(projectId: string, categoryId: string, data: { name?: string; planned_amount?: number }) {
    const updated = await projectsAPI.updateCategory(projectId, categoryId, data)

    // Helper to update a category in a categories array
    const updateInArray = (categories: ProjectCategoryWithSpent[]) => {
      const idx = categories.findIndex(c => c.id === categoryId)
      if (idx !== -1) {
        const existing = categories[idx]!
        categories[idx] = {
          id: existing.id,
          project_id: existing.project_id,
          name: updated.name,
          planned_amount: updated.planned_amount,
          created_at: existing.created_at,
          total_spent: existing.total_spent,
          remaining: updated.planned_amount - existing.total_spent,
        }
      }
    }

    // Update in currentProject
    if (currentProject.value?.id === projectId) {
      updateInArray(currentProject.value.categories)
    }

    // Also update in projects list (used by HistoryView for category options)
    const projectInList = projects.value.find(p => p.id === projectId)
    if (projectInList) {
      updateInArray(projectInList.categories)
    }

    return updated
  }

  async function deleteCategory(projectId: string, categoryId: string) {
    await projectsAPI.deleteCategory(projectId, categoryId)

    // Update in currentProject
    if (currentProject.value?.id === projectId) {
      currentProject.value.categories = currentProject.value.categories.filter(c => c.id !== categoryId)
    }

    // Also update in projects list
    const projectInList = projects.value.find(p => p.id === projectId)
    if (projectInList) {
      projectInList.categories = projectInList.categories.filter(c => c.id !== categoryId)
    }
  }

  // ── Planned Expenses ──

  async function fetchPlannedExpenses(projectId: string) {
    plannedExpenses.value = await projectsAPI.getPlannedExpenses(projectId)
  }

  async function createPlannedExpense(projectId: string, data: { project_category_id: string; description: string; amount: number; due_date?: string; reminder_date?: string }) {
    const expense = await projectsAPI.createPlannedExpense(projectId, data)
    plannedExpenses.value.push(expense)
    return expense
  }

  async function updatePlannedExpense(projectId: string, expenseId: string, data: {
    project_category_id?: string; description?: string; amount?: number;
    due_date?: string; reminder_date?: string; status?: string;
    transaction_id?: string; pro_transaction_id?: string
  }) {
    const updated = await projectsAPI.updatePlannedExpense(projectId, expenseId, data)
    const idx = plannedExpenses.value.findIndex(e => e.id === expenseId)
    if (idx !== -1) plannedExpenses.value[idx] = updated
    return updated
  }

  async function deletePlannedExpense(projectId: string, expenseId: string) {
    await projectsAPI.deletePlannedExpense(projectId, expenseId)
    plannedExpenses.value = plannedExpenses.value.filter(e => e.id !== expenseId)
  }

  // ── Transactions ──

  async function fetchProjectTransactions(projectId: string) {
    projectTransactions.value = await projectsAPI.getTransactions(projectId)
  }

  // ── Reminders ──

  async function fetchReminders() {
    reminders.value = await projectsAPI.getReminders()
  }

  // ── Members ──

  const members = ref<ProjectMemberWithUser[]>([])
  const memberBalances = ref<ProjectMemberBalance[]>([])
  const projectInvitations = ref<ProjectInvitationWithDetails[]>([])

  async function fetchMembers(projectId: string) {
    members.value = await projectsAPI.getMembers(projectId)
  }

  async function inviteMember(projectId: string, email: string, role: string = 'member') {
    await projectsAPI.inviteMember(projectId, email, role)
  }

  async function removeMember(projectId: string, memberId: string) {
    await projectsAPI.removeMember(projectId, memberId)
    members.value = members.value.filter(m => m.id !== memberId)
  }

  async function updateMemberShare(projectId: string, memberId: string, share: number) {
    const updated = await projectsAPI.updateMemberShare(projectId, memberId, share)
    const idx = members.value.findIndex(m => m.id === memberId)
    if (idx !== -1) members.value[idx] = updated
    return updated
  }

  async function fetchMemberBalances(projectId: string) {
    memberBalances.value = await projectsAPI.getBalances(projectId)
  }

  async function fetchProjectInvitations() {
    projectInvitations.value = await projectsAPI.getMyInvitations()
  }

  async function acceptProjectInvitation(invitationId: string) {
    await projectsAPI.acceptInvitation(invitationId)
    projectInvitations.value = projectInvitations.value.filter(i => i.id !== invitationId)
  }

  async function rejectProjectInvitation(invitationId: string) {
    await projectsAPI.rejectInvitation(invitationId)
    projectInvitations.value = projectInvitations.value.filter(i => i.id !== invitationId)
  }

  return {
    projects, summaries, currentProject, plannedExpenses, projectTransactions, reminders, loading,
    members, memberBalances, projectInvitations,
    fetchProjects, fetchSummaries, fetchProject,
    createProject, updateProject, deleteProject,
    createCategory, updateCategory, deleteCategory,
    fetchPlannedExpenses, createPlannedExpense, updatePlannedExpense, deletePlannedExpense,
    fetchProjectTransactions, fetchReminders,
    fetchMembers, inviteMember, removeMember, updateMemberShare, fetchMemberBalances,
    fetchProjectInvitations, acceptProjectInvitation, rejectProjectInvitation,
  }
})
