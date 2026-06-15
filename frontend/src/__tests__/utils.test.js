import { describe, it, expect } from 'vitest'
import { formatMoisKey, formatJ, MOIS_LABELS } from '../utils'

describe('MOIS_LABELS', () => {
  it('contient 12 entrées', () => {
    expect(MOIS_LABELS).toHaveLength(12)
  })

  it('commence par Jan', () => {
    expect(MOIS_LABELS[0]).toBe('Jan')
  })

  it('se termine par Déc', () => {
    expect(MOIS_LABELS[11]).toBe('Déc')
  })

  it('ne contient pas de doublons', () => {
    const uniques = new Set(MOIS_LABELS)
    expect(uniques.size).toBe(12)
  })
})

describe('formatMoisKey', () => {
  it('formate YYYY-01 en Jan XX', () => {
    expect(formatMoisKey('2025-01')).toBe('Jan 25')
  })

  it('formate YYYY-12 en Déc XX', () => {
    expect(formatMoisKey('2025-12')).toBe('Déc 25')
  })

  it('formate YYYY-06 en Jun XX', () => {
    expect(formatMoisKey('2024-06')).toBe('Jun 24')
  })

  it('abrège l\'année sur 2 chiffres', () => {
    expect(formatMoisKey('2030-03')).toBe('Mar 30')
  })

  it('retourne — pour null', () => {
    expect(formatMoisKey(null)).toBe('—')
  })

  it('retourne — pour undefined', () => {
    expect(formatMoisKey(undefined)).toBe('—')
  })

  it('retourne — pour chaîne vide', () => {
    expect(formatMoisKey('')).toBe('—')
  })
})

describe('formatJ', () => {
  it('retourne - pour null', () => {
    expect(formatJ(null)).toBe('-')
  })

  it('retourne - pour undefined', () => {
    expect(formatJ(undefined)).toBe('-')
  })

  it('formate zéro avec 2 décimales', () => {
    const result = formatJ(0)
    expect(result).toMatch(/0[,.]00/)
  })

  it('formate un entier avec ,00', () => {
    const result = formatJ(5)
    expect(result).toMatch(/5[,.]00/)
  })

  it('formate 3.1 avec 2 décimales', () => {
    const result = formatJ(3.1)
    expect(result).toMatch(/3[,.]10/)
  })

  it('retourne une chaîne pour un grand nombre', () => {
    const result = formatJ(1234.56)
    expect(typeof result).toBe('string')
    expect(result.replace(/\s/g, '')).toMatch(/1.?234/)
  })
})
