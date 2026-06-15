import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/client', () => ({
  api: {
    getEvolutions: vi.fn(),
    getReleases: vi.fn().mockResolvedValue([]),
    getEquipes: vi.fn().mockResolvedValue([]),
  },
}))

import Evolutions from '../pages/Evolutions'
import { api } from '../api/client'

describe('Evolutions', () => {
  beforeEach(() => {
    api.getEvolutions.mockResolvedValue([])
  })

  it('se charge sans erreur (liste vide)', async () => {
    render(
      <MemoryRouter>
        <Evolutions />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Évolutions')).toBeInTheDocument()
    })
  })

  it('affiche les évolutions récupérées', async () => {
    api.getEvolutions.mockResolvedValue([
      {
        code: 'ASD-E-001',
        libelle: 'Mon évolution',
        code_equipe: 'EQ01',
        code_release: null,
        type_evolution: 'Roadmap',
        statut_aha: 'En cours',
        budget: 10,
        macro_chiffrage: null,
        temps_dev: 0,
        temps_testing: 0,
        avancement_moyen: 0,
      },
    ])

    render(
      <MemoryRouter>
        <Evolutions />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('ASD-E-001')).toBeInTheDocument()
    })
  })

  it('ne crash pas quand libelle est null (garde || "")', async () => {
    api.getEvolutions.mockResolvedValue([
      {
        code: 'ASD-E-002',
        libelle: null,
        code_equipe: 'EQ01',
        code_release: null,
        type_evolution: null,
        statut_aha: 'En cours',
        budget: null,
        macro_chiffrage: null,
        temps_dev: 0,
        temps_testing: 0,
        avancement_moyen: 0,
      },
    ])

    // Le composant filtre avec (e.libelle || '').toLowerCase() — ne doit pas lancer
    expect(() =>
      render(
        <MemoryRouter>
          <Evolutions />
        </MemoryRouter>
      )
    ).not.toThrow()
  })
})
