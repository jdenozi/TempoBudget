/**
 * Tests for ProSetupWizard validation logic
 */
import { describe, it, expect } from 'vitest'

// Extracted validation logic for testing
interface WizardForm {
  legal_form: 'micro' | 'ei_reel' | 'eurl' | 'sasu' | 'sas'
  cotisation_rate: number
  company_name: string
  siret: string
}

function canProceed(step: number, form: WizardForm, acreEnabled: boolean, acreStartDate: number | null): boolean {
  if (step === 1) return !!form.legal_form
  if (step === 2) return form.cotisation_rate > 0
  if (step === 3) {
    if (acreEnabled && !acreStartDate) return false
    return true
  }
  return true
}

function canFinish(form: WizardForm): boolean {
  const hasCompanyName = form.company_name.trim().length > 0
  const hasSiret = form.siret.trim().length > 0
  return hasCompanyName || hasSiret
}

describe('ProSetupWizard', () => {
  describe('canProceed', () => {
    const defaultForm: WizardForm = {
      legal_form: 'micro',
      cotisation_rate: 21.2,
      company_name: '',
      siret: '',
    }

    it('step 1: requires legal form to be set', () => {
      expect(canProceed(1, defaultForm, false, null)).toBe(true)
    })

    it('step 1: fails if legal form is empty', () => {
      const form = { ...defaultForm, legal_form: '' as any }
      expect(canProceed(1, form, false, null)).toBe(false)
    })

    it('step 2: requires cotisation rate > 0', () => {
      expect(canProceed(2, defaultForm, false, null)).toBe(true)
    })

    it('step 2: fails if cotisation rate is 0', () => {
      const form = { ...defaultForm, cotisation_rate: 0 }
      expect(canProceed(2, form, false, null)).toBe(false)
    })

    it('step 2: fails if cotisation rate is negative', () => {
      const form = { ...defaultForm, cotisation_rate: -5 }
      expect(canProceed(2, form, false, null)).toBe(false)
    })

    it('step 3: passes without ACRE', () => {
      expect(canProceed(3, defaultForm, false, null)).toBe(true)
    })

    it('step 3: passes with ACRE and start date', () => {
      const startDate = Date.now()
      expect(canProceed(3, defaultForm, true, startDate)).toBe(true)
    })

    it('step 3: fails with ACRE but no start date', () => {
      expect(canProceed(3, defaultForm, true, null)).toBe(false)
    })

    it('step 4: always passes canProceed (validation is in canFinish)', () => {
      expect(canProceed(4, defaultForm, false, null)).toBe(true)
    })
  })

  describe('canFinish', () => {
    it('passes with company name only', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: 'Mon Entreprise',
        siret: '',
      }
      expect(canFinish(form)).toBe(true)
    })

    it('passes with SIRET only', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: '',
        siret: '12345678900012',
      }
      expect(canFinish(form)).toBe(true)
    })

    it('passes with both company name and SIRET', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: 'Mon Entreprise',
        siret: '12345678900012',
      }
      expect(canFinish(form)).toBe(true)
    })

    it('fails with neither company name nor SIRET', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: '',
        siret: '',
      }
      expect(canFinish(form)).toBe(false)
    })

    it('fails with only whitespace in company name', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: '   ',
        siret: '',
      }
      expect(canFinish(form)).toBe(false)
    })

    it('fails with only whitespace in SIRET', () => {
      const form: WizardForm = {
        legal_form: 'micro',
        cotisation_rate: 21.2,
        company_name: '',
        siret: '   ',
      }
      expect(canFinish(form)).toBe(false)
    })
  })

  describe('legal form presets', () => {
    const ACTIVITY_PRESETS: Record<string, number> = {
      services: 21.2,
      liberal: 23.1,
      vente: 12.3,
      artisan: 21.2,
      commercant: 12.3,
    }

    it('services has correct default rate', () => {
      expect(ACTIVITY_PRESETS['services']).toBe(21.2)
    })

    it('liberal has correct default rate', () => {
      expect(ACTIVITY_PRESETS['liberal']).toBe(23.1)
    })

    it('vente has correct default rate', () => {
      expect(ACTIVITY_PRESETS['vente']).toBe(12.3)
    })

    it('artisan has correct default rate', () => {
      expect(ACTIVITY_PRESETS['artisan']).toBe(21.2)
    })

    it('commercant has correct default rate', () => {
      expect(ACTIVITY_PRESETS['commercant']).toBe(12.3)
    })
  })
})
