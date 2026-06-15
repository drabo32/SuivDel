import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockDashboardData = {
  evolutions: [],
  recette_interne: null,
  par_equipe_livraison: {},
  par_equipe_testing: {},
  hors_evol_total: 0,
  hors_evol_raf_total: 0,
  evol_raf_total: 0,
  raf_global_total: 0,
  hors_evol_taches: [],
}

vi.mock('../api/client', () => ({
  api: {
    getDashboardPrincipal: vi.fn(),
    getEquipes: vi.fn().mockResolvedValue([]),
    getReleases: vi.fn().mockResolvedValue([]),
    updateRafHorsEvolution: vi.fn().mockResolvedValue({}),
  },
}))

import Dashboard from '../pages/Dashboard'
import { api } from '../api/client'

describe('Dashboard', () => {
  beforeEach(() => {
    api.getDashboardPrincipal.mockResolvedValue(mockDashboardData)
  })

  it('se charge sans erreur', async () => {
    const { container } = render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(container.firstChild).toBeInTheDocument()
    })
  })

  it('ne crash pas quand recette_interne est null (garde ?? {})', async () => {
    // Sans la garde `data.recette_interne ?? {}`, Object.entries(null) lèverait TypeError
    api.getDashboardPrincipal.mockResolvedValue({
      ...mockDashboardData,
      recette_interne: null,
    })

    let renderError = null
    try {
      const { unmount } = render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      )
      // Attendre que useEffect charge les données
      await waitFor(() => {
        expect(api.getDashboardPrincipal).toHaveBeenCalled()
      })
      unmount()
    } catch (e) {
      renderError = e
    }

    expect(renderError).toBeNull()
  })

  it('ne crash pas quand par_equipe_livraison est vide', async () => {
    api.getDashboardPrincipal.mockResolvedValue({
      ...mockDashboardData,
      par_equipe_livraison: {},
      par_equipe_testing: {},
    })

    expect(() =>
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      )
    ).not.toThrow()
  })
})
