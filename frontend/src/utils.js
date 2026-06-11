export const MOIS_LABELS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

export const formatMoisKey = (k) => {
  if (!k) return '—'
  const [annee, mois] = k.split('-')
  return `${MOIS_LABELS[parseInt(mois) - 1]} ${annee.slice(2)}`
}

export const formatJ = v => v != null ? Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'
