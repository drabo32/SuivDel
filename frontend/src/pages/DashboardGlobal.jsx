import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Select, Space, Typography } from 'antd'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '../api/client'

const { Title } = Typography
const COULEURS = ['#1677ff', '#52c41a', '#fa8c16', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#faad14', '#a0d911']

export default function DashboardGlobal() {
  const [data, setData] = useState(null)
  const [releases, setReleases] = useState([])
  const [equipes, setEquipes] = useState([])
  const [filtres, setFiltres] = useState({})

  const charger = (params = {}) => api.getDashboardGlobal(params).then(setData)

  useEffect(() => {
    charger()
    api.getReleases().then(setReleases)
    api.getEquipes().then(e => setEquipes(e.filter(eq => eq.type_equipe === 'DEV')))
  }, [])

  const appliquer = (val, cle) => {
    const f = { ...filtres, [cle]: val }
    setFiltres(f)
    charger(Object.fromEntries(Object.entries(f).filter(([, v]) => v)))
  }

  if (!data) return null

  const donneesEquipes = Object.keys(data.temps_dev_par_equipe).map(eq => ({
    equipe: equipes.find(e => e.code === eq)?.libelle || eq,
    'Temps DEV': data.temps_dev_par_equipe[eq],
    'Budget Aha': data.budget_par_equipe?.[eq] || 0,
    'Macro chiffrage': data.macro_par_equipe[eq] || 0,
  }))

  const donneesEtapes = Object.entries(data.avancement_etapes).map(([etape, statuts]) => ({
    etape: etape.replace('Recette Pôle Testing', 'Recette PT').replace('Livraison intégration', 'Livraison'),
    ...statuts,
  }))

  return (
    <div>
      <Title level={3}>Dashboard global</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select placeholder="Release" style={{ width: 200 }} allowClear onChange={v => appliquer(v, 'release')}
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))} />
        <Select placeholder="Équipe" style={{ width: 160 }} allowClear onChange={v => appliquer(v, 'equipe')}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))} />
      </Space>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="Total évolutions" value={data.total} /></Card></Col>
        {Object.entries(data.statuts_aha).map(([statut, nb]) => (
          <Col span={4} key={statut}><Card><Statistic title={statut} value={nb} /></Card></Col>
        ))}
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Temps DEV vs Budget Aha vs Macro chiffrage par équipe (jours)">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={donneesEquipes}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="equipe" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Temps DEV" fill="#1677ff" />
                <Bar dataKey="Budget Aha" fill="#fa8c16" />
                <Bar dataKey="Macro chiffrage" fill="#d9d9d9" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Avancement par étape">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={donneesEtapes} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="etape" type="category" width={110} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="À faire" fill="#d9d9d9" stackId="a" />
                <Bar dataKey="En cours" fill="#1677ff" stackId="a" />
                <Bar dataKey="Terminé" fill="#52c41a" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
