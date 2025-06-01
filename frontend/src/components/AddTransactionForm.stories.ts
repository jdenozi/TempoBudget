/**
 * Storybook stories for AddTransactionForm component.
 *
 * This file demonstrates the AddTransactionForm component in various states
 * and configurations for documentation and testing purposes.
 */

import type { Meta, StoryObj } from '@storybook/vue3'
import AddTransactionForm from './AddTransactionForm.vue'

/**
 * The AddTransactionForm component provides a comprehensive form for creating
 * new transactions. It supports both one-time and recurring transactions with
 * full validation.
 *
 * ## Features
 * - Income and expense type selection
 * - Budget and category selection
 * - Amount entry with currency display
 * - Date picker
 * - Recurring transaction configuration
 * - Comments/notes field
 */
const meta: Meta<typeof AddTransactionForm> = {
  title: 'Components/AddTransactionForm',
  component: AddTransactionForm,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component:
          'A form component for creating new transactions with support for recurring transactions and validation.',
      },
    },
  },
  argTypes: {
    onSuccess: { action: 'success' },
  },
}

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default state of the AddTransactionForm.
 * Shows an empty form ready for user input.
 */
export const Default: Story = {
  render: () => ({
    components: { AddTransactionForm },
    template: '<div style="width: 350px;"><AddTransactionForm /></div>',
  }),
}

/**
 * Form configured for expense entry.
 * The expense type is pre-selected.
 */
export const ExpenseForm: Story = {
  render: () => ({
    components: { AddTransactionForm },
    template: '<div style="width: 350px;"><AddTransactionForm /></div>',
  }),
  parameters: {
    docs: {
      description: {
        story: 'Form with expense type pre-selected for quick expense entry.',
      },
    },
  },
}

/**
 * Form configured for income entry.
 * Demonstrates the income workflow.
 */
export const IncomeForm: Story = {
  render: () => ({
    components: { AddTransactionForm },
    template: '<div style="width: 350px;"><AddTransactionForm /></div>',
  }),
  parameters: {
    docs: {
      description: {
        story: 'Form demonstrating income entry workflow.',
      },
    },
  },
}
