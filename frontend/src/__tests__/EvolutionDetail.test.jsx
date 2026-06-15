import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../api/client', () => ({
  api: {
    getEvolution: vi.fn().mockResolvedValue({
      code: 'ASD-E-001',
      libelle: 'Mon évolution',
      code_equipe: 'EQ01',
      code_release: null,
      type_evolution: 'Roadmap',
      statut_aha: 'En cours',
      budget: null,
      macro_chiffrage: null,
      chiffrage_edition: null,
      raf_dev: 5,
      raf_testing: 2,
      conso_2025: null,
      version_verrou: 0,
      etapes: [],
    }),
    getTempsEvolution: vi.fn().mockResolvedValue({
      dev_total: 0,
      testing_total: 0,
      par_mois_dev: {},
      par_mois_testing: {},
      detail: [],
    }),
    getSnapshots: vi.fn().mockResolvedValue([]),
    getHistoriqueEtapes: vi.fn().mockResolvedValue([]),
    getReleases: vi.fn().mockResolvedValue([]),
    getEquipes: vi.fn().mockResolvedValue([]),
    updateEvolution: vi.fn().mockResolvedValue({ ok: true, version_verrou: 1 }),
    updateEtape: vi.fn().mockResolvedValue({ ok: true }),
    deleteSnapshot: vi.fn().mockResolvedValue({}),
  },
}))

import EvolutionDetail from '../pages/EvolutionDetail'

function renderAvecRoute() {
  return render(
    <MemoryRouter initialEntries={['/evolutions/ASD-E-001']}>
      <Routes>
        <Route path="/evolutions/:code" element={<EvolutionDetail />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('EvolutionDetail', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })

  it('affiche le libellé de l\'évolution après chargement', async () => {
    renderAvecRoute()
    // Le titre rend "ASD-E-001 — Mon évolution" → utiliser une regex
    await waitFor(() => {
      expect(screen.getByText(/Mon évolution/)).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('le bouton Retour appelle navigate(-1)', async () => {
    renderAvecRoute()
    await waitFor(() => {
      expect(screen.getByText(/Mon évolution/)).toBeInTheDocument()
    }, { timeout: 5000 })

    const backBtn = screen.getByText('Retour')
    fireEvent.click(backBtn)

    expect(mockNavigate).toHaveBeenCalledWith(-1)
    expect(mockNavigate).not.toHaveBeenCalledWith('/evolutions')
  })

  it('ne crash pas quand les listes de données sont vides', async () => {
    expect(() => renderAvecRoute()).not.toThrow()
  })
})
