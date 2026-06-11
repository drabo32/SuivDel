const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (res.status === 409) throw new Error('Conflit de concurrence — rechargez les données')
  if (!res.ok) throw new Error(`Erreur ${res.status}`)
  return res.json()
}

export const api = {
  // Evolutions
  getEvolutions: (params = {}) => request('/evolutions?' + new URLSearchParams(params)),
  getEvolution: (code) => request(`/evolutions/${code}`),
  updateEvolution: (code, data) => request(`/evolutions/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
  getTempsEvolution: (code) => request(`/evolutions/${code}/temps`),

  // Etapes
  updateEtape: (id, data) => request(`/etapes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getHistoriqueEtapes: (code) => request(`/etapes/historique/${code}`),

  // Snapshots
  getSnapshots: (code) => request(`/snapshots/${code}`),
  deleteSnapshot: (id) => request(`/snapshots/${id}`, { method: 'DELETE' }),

  // Imports
  importAha: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/aha`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  importChangepoint: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/changepoint`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  importInit: (file) => {
    const form = new FormData(); form.append('file', file)
    return fetch(`${BASE}/imports/init`, { method: 'POST', body: form })
      .then(async r => { if (!r.ok) throw new Error(await r.text()); return r.json() })
  },
  getHistoriqueImports: () => request('/imports/historique'),

  // Dashboards
  getDashboardPrincipal: (params = {}) => request('/dashboards/principal?' + new URLSearchParams(params)),
  getDashboardGlobal: (params = {}) => request('/dashboards/global?' + new URLSearchParams(params)),
  getDashboardEquipe: (code, params = {}) => request(`/dashboards/equipe/${code}?` + new URLSearchParams(params)),
  getDashboardTesting: (params = {}) => request('/dashboards/testing?' + new URLSearchParams(params)),
  getDashboardAtterrissage: (params = {}) => request('/dashboards/atterrissage?' + new URLSearchParams(params)),
  getDashboardRelease: (code) => request(`/dashboards/release/${code}`),
  getHistoriqueRelease: (code) => request(`/dashboards/release/${code}/historique`),
  getHorsEvolutions: (params = {}) => request('/dashboards/hors-evolutions?' + new URLSearchParams(params)),
  getControleAha: () => request('/dashboards/controle-aha'),
  updateRafHorsEvolution: (time_niv2, nom_tache, raf) =>
    request(`/dashboards/hors-evolutions-raf?time_niv2=${encodeURIComponent(time_niv2)}&nom_tache=${encodeURIComponent(nom_tache)}&raf=${raf}`, { method: 'PUT' }),

  // Admin
  getEquipes: () => request('/admin/equipes'),
  getReleases: () => request('/admin/releases'),
  createRelease: (data) => request('/admin/releases', { method: 'POST', body: JSON.stringify(data) }),
  updateRelease: (code, data) => request(`/admin/releases/${code}`, { method: 'PUT', body: JSON.stringify(data) }),
  getWorkspaces: () => request('/admin/workspaces'),
  updateWorkspace: (workspace, code_equipe) =>
    request(`/admin/workspaces/${encodeURIComponent(workspace)}?code_equipe=${code_equipe}`, { method: 'PUT' }),
  getRessources: () => request('/admin/ressources'),
  saveRessource: (data) => request('/admin/ressources', { method: 'POST', body: JSON.stringify(data) }),
  deleteRessource: (matricule) => request(`/admin/ressources/${matricule}`, { method: 'DELETE' }),
  getTimeNiv2Mappings: () => request('/admin/time-niv2'),
  saveTimeNiv2Mapping: (time_niv2, code_equipe, type_equipe) =>
    request(`/admin/time-niv2?time_niv2=${encodeURIComponent(time_niv2)}&code_equipe=${code_equipe}&type_equipe=${type_equipe}`, { method: 'POST' }),
  deleteTimeNiv2Mapping: (time_niv2) => request(`/admin/time-niv2/${encodeURIComponent(time_niv2)}`, { method: 'DELETE' }),
}
