/**
 * Tests for HelpChat keyword matching logic
 */
import { describe, it, expect } from 'vitest'

// Extracted keyword matching logic for testing
interface HelpTopic {
  key: string
  keywords: string[]
  response: string
}

function findResponse(input: string, topics: HelpTopic[], notFoundResponse: string): string {
  const lowerInput = input.toLowerCase()

  for (const topic of topics) {
    for (const keyword of topic.keywords) {
      if (lowerInput.includes(keyword.toLowerCase())) {
        return topic.response
      }
    }
  }

  return notFoundResponse
}

describe('HelpChat', () => {
  const mockTopics: HelpTopic[] = [
    {
      key: 'invoice',
      keywords: ['facture', 'invoice', 'créer facture', 'facturer'],
      response: 'Response about invoices',
    },
    {
      key: 'quote',
      keywords: ['devis', 'quote', 'créer devis'],
      response: 'Response about quotes',
    },
    {
      key: 'acre',
      keywords: ['acre', 'aide', 'création', 'réduction'],
      response: 'Response about ACRE',
    },
    {
      key: 'cotisations',
      keywords: ['cotisation', 'urssaf', 'charges'],
      response: 'Response about cotisations',
    },
  ]

  const notFound = 'No response found'

  describe('findResponse', () => {
    it('finds response for exact keyword match', () => {
      const response = findResponse('facture', mockTopics, notFound)
      expect(response).toBe('Response about invoices')
    })

    it('finds response for keyword in sentence', () => {
      const response = findResponse('Comment créer une facture ?', mockTopics, notFound)
      expect(response).toBe('Response about invoices')
    })

    it('is case insensitive', () => {
      const response = findResponse('FACTURE', mockTopics, notFound)
      expect(response).toBe('Response about invoices')
    })

    it('matches partial keywords', () => {
      const response = findResponse('Je veux facturer un client', mockTopics, notFound)
      expect(response).toBe('Response about invoices')
    })

    it('returns notFound for unknown input', () => {
      const response = findResponse('blabla random text', mockTopics, notFound)
      expect(response).toBe(notFound)
    })

    it('matches ACRE keywords', () => {
      const response = findResponse("C'est quoi l'ACRE ?", mockTopics, notFound)
      expect(response).toBe('Response about ACRE')
    })

    it('matches URSSAF keywords', () => {
      const response = findResponse('Comment payer URSSAF', mockTopics, notFound)
      expect(response).toBe('Response about cotisations')
    })

    it('returns first match when multiple keywords match', () => {
      // Invoice comes before quote in the topics array
      const response = findResponse('facture et devis', mockTopics, notFound)
      expect(response).toBe('Response about invoices')
    })

    it('handles empty input', () => {
      const response = findResponse('', mockTopics, notFound)
      expect(response).toBe(notFound)
    })

    it('handles special characters in input', () => {
      const response = findResponse("C'est quoi les cotisations???", mockTopics, notFound)
      expect(response).toBe('Response about cotisations')
    })
  })
})
