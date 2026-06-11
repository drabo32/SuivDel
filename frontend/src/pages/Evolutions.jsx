import React, { useState, useEffect } from 'react'
import { Table, Select, Input, Space, Tag, Typography, Button, Tooltip } from 'antd'
import { EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const { Title } = Typography

const COULEUR_STATUT = { 'Terminée': 'green', 'En cours': 'blue', 'Abandonnée': 'red', 'Idée': 'default', 'A instruire': 'orange' }
const COULEUR_TYPE = { 'Réglementaire': 'purple', 'Roadmap': 'cyan', 'Dédié': 'gold' }

export default function Evolutions() {
  const [evolutions, setEvolutions] = useState([])
  const [releases, setReleases] = useState([])
  const [equipes, setEquipes] = useState([])
  const [loading, setLoading] = useState(false)
  const [filtres, setFiltres] = useState({})
  const [recherche, setRecherche] = useState('')
  const navigate = useNavigate()

  const charger = (params = {}) => {
    setLoading(true)
    api.getEvolutions(params).then(setEvolutions).finally(() => setLoading(false))
  }

  useEffect(() => {
    charger()
    api.getReleases().then(setReleases)
    api.getEquipes().then(setEquipes)
  }, [])

  const appliquerFiltres = (nouveaux) => {
    const f = { ...filtres, ...nouveaux }
    setFiltres(f)
    const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v))
    charger(params)
  }

  const donneesFiltrees = evolutions.filter(e =>
    !recherche || e.code.toLowerCase().includes(recherche.toLowerCase()) ||
    e.libelle.toLowerCase().includes(recherche.toLowerCase())
  )

  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, fixed: 'left' },
    { title: 'Libellé', dataIndex: 'libelle', key: 'libelle', ellipsis: true },
    { title: 'Équipe', dataIndex: 'code_equipe', key: 'equipe', width: 110, render: v => equipes.find(e => e.code === v)?.libelle || v },
    { title: 'Version', dataIndex: 'code_release', key: 'release', width: 110 },
    { title: 'Type', dataIndex: 'type_evolution', key: 'type', width: 110, render: v => v ? <Tag color={COULEUR_TYPE[v]}>{v}</Tag> : '-' },
    { title: 'Statut Aha', dataIndex: 'statut_aha', key: 'statut', width: 110, render: v => v ? <Tag color={COULEUR_STATUT[v]}>{v}</Tag> : '-' },
    { title: 'Budget Aha (j)', dataIndex: 'budget', key: 'budget', width: 100, render: v => v ?? '-', align: 'right' },
    { title: 'Macro chiff. (j)', dataIndex: 'macro_chiffrage', key: 'macro', width: 110, render: v => v ?? '-', align: 'right' },
    { title: 'Tps DEV (j)', dataIndex: 'temps_dev', key: 'tdev', width: 100, render: v => v ?? 0, align: 'right' },
    { title: 'Tps Test (j)', dataIndex: 'temps_testing', key: 'ttest', width: 100, render: v => v ?? 0, align: 'right' },
    { title: 'Avanc. %', dataIndex: 'avancement_moyen', key: 'av', width: 85, render: v => `${v}%`, align: 'right' },
    {
      title: '', key: 'actions', width: 50, fixed: 'right',
      render: (_, r) => (
        <Tooltip title="Voir détail">
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/evolutions/${r.code}`)} />
        </Tooltip>
      )
    },
  ]

  return (
    <div>
      <Title level={3}>Évolutions</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input.Search placeholder="Rechercher code / libellé" style={{ width: 250 }} onSearch={setRecherche} onChange={e => !e.target.value && setRecherche('')} allowClear />
        <Select placeholder="Équipe" style={{ width: 160 }} allowClear onChange={v => appliquerFiltres({ equipe: v })}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))} />
        <Select placeholder="Release" style={{ width: 180 }} allowClear onChange={v => appliquerFiltres({ release: v })}
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))} />
        <Select placeholder="Type" style={{ width: 150 }} allowClear onChange={v => appliquerFiltres({ type_evolution: v })}
          options={['Réglementaire', 'Roadmap', 'Dédié'].map(t => ({ value: t, label: t }))} />
        <Select placeholder="Statut Aha" style={{ width: 150 }} allowClear onChange={v => appliquerFiltres({ statut_aha: v })}
          options={['En cours', 'Terminée', 'Abandonnée', 'Idée', 'A instruire'].map(s => ({ value: s, label: s }))} />
      </Space>
      <Table
        dataSource={donneesFiltrees}
        columns={colonnes}
        rowKey="code"
        loading={loading}
        size="small"
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 25, showTotal: (t) => `${t} évolutions` }}
        onRow={(r) => ({ onDoubleClick: () => navigate(`/evolutions/${r.code}`) })}
      />
    </div>
  )
}
