import React, { useState, useEffect, useMemo } from 'react'
import { Card, Select, Table, Tag, Row, Col, Typography, Space } from 'antd'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const { Title } = Typography
const COULEUR_STATUT = { 'À faire': '#d9d9d9', 'En cours': '#1677ff', 'Terminé': '#52c41a' }

function BarreStatuts({ data, titre }) {
  const equipes = Object.keys(data)
  const donneesChart = equipes.map(eq => ({
    equipe: eq,
    'À faire': data[eq]['À faire'] || 0,
    'En cours': data[eq]['En cours'] || 0,
    'Terminé': data[eq]['Terminé'] || 0,
  }))
  return (
    <Card title={titre}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={donneesChart}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="equipe" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Legend />
          {Object.entries(COULEUR_STATUT).map(([s, c]) => <Bar key={s} dataKey={s} fill={c} stackId="a" />)}
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}

const formatJ = v => v != null ? Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '-'

export default function DashboardRelease() {
  const [releases, setReleases] = useState([])
  const [releaseSelectionnee, setReleaseSelectionnee] = useState(null)
  const [data, setData] = useState(null)
  const [filtreEquipe, setFiltreEquipe] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { api.getReleases().then(setReleases) }, [])

  const charger = (code) => {
    if (!code) return
    api.getDashboardRelease(code).then(setData)
  }

  const evolutionsFiltrees = useMemo(() => {
    if (!data) return []
    if (!filtreEquipe) return data.evolutions
    return data.evolutions.filter(e => e.equipe === filtreEquipe)
  }, [data, filtreEquipe])

  const equipesDisponibles = useMemo(() => {
    if (!data) return []
    return [...new Set(data.evolutions.map(e => e.equipe))].sort()
  }, [data])

  // Données graphique synthétique par évolution
  const donneesChart = evolutionsFiltrees.map(e => ({
    code: e.code,
    'Budget': e.budget || 0,
    'Chiff. édition': e.chiffrage_edition || 0,
    'Consommé': e.consomme_total || 0,
    'RAF': e.raf_total || 0,
  }))

  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, render: v => <a onClick={() => navigate(`/evolutions/${v}`)}>{v}</a> },
    { title: 'Libellé', dataIndex: 'libelle', key: 'lib', ellipsis: true },
    { title: 'Équipe', dataIndex: 'equipe', key: 'eq', width: 100 },
    { title: 'Statut Aha', dataIndex: 'statut_aha', key: 'st', width: 100, render: v => <Tag>{v}</Tag> },
    { title: 'Budget (j)', dataIndex: 'budget', key: 'budget', width: 90, align: 'right', render: formatJ },
    { title: 'Macro (j)', dataIndex: 'macro_chiffrage', key: 'mc', width: 85, align: 'right', render: formatJ },
    { title: 'Chiff. éd. (j)', dataIndex: 'chiffrage_edition', key: 'ce', width: 95, align: 'right', render: formatJ },
    { title: 'Consommé (j)', dataIndex: 'consomme_total', key: 'cons', width: 105, align: 'right', render: formatJ },
    { title: 'RAF Total (j)', dataIndex: 'raf_total', key: 'raf', width: 100, align: 'right', render: formatJ },
    { title: 'Atterrissage (j)', dataIndex: 'atterrissage', key: 'att', width: 115, align: 'right',
      render: v => <strong style={{ color: '#1677ff' }}>{formatJ(v)}</strong> },
    { title: 'Avanc. %', dataIndex: 'avancement_moyen', key: 'av', width: 80, align: 'right', render: v => `${v}%` },
    ...['Recette interne', 'Livraison intégration', 'Recette Pôle Testing'].map(e => ({
      title: e.replace('Recette Pôle Testing', 'Rec. PT').replace('Livraison intégration', 'Livraison'),
      key: e, width: 85,
      render: (_, r) => {
        const s = r.etapes?.[e]
        return s ? <Tag color={COULEUR_STATUT[s]} style={{ fontSize: 11 }}>{s}</Tag> : '-'
      }
    })),
  ]

  // Hauteur dynamique du graphique selon le nombre d'évolutions
  const chartHeight = Math.max(300, evolutionsFiltrees.length * 32)

  return (
    <div>
      <Title level={3}>Dashboard par release</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select placeholder="Choisir une release" style={{ width: 260 }}
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))}
          onChange={v => { setReleaseSelectionnee(v); setFiltreEquipe(null); charger(v) }} />
        <Select placeholder="Équipe" style={{ width: 180 }} allowClear value={filtreEquipe}
          options={equipesDisponibles.map(e => ({ value: e, label: e }))}
          onChange={v => setFiltreEquipe(v || null)} />
      </Space>

      {data && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <BarreStatuts data={data.par_equipe_livraison} titre="Livraison intégration par équipe" />
            </Col>
            <Col span={8}>
              <BarreStatuts data={data.par_equipe_testing} titre="Recette Pôle Testing par équipe" />
            </Col>
            <Col span={8}>
              <Card title="RAF total par équipe (jours)">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={Object.entries(data.raf_par_equipe).map(([eq, v]) => ({ equipe: eq, 'RAF Total': v }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="equipe" tick={{ fontSize: 11 }} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="RAF Total" fill="#fa8c16" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          <Card title={`Synthèse par évolution — Budget / Atterrissage / Consommé / RAF (${evolutionsFiltrees.length})`} style={{ marginBottom: 16 }}>
            <div style={{ overflowY: 'auto', maxHeight: 420 }}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <BarChart data={donneesChart} layout="vertical" margin={{ left: 90, right: 20, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tick={{ fontSize: 11 }} unit=" j" />
                  <YAxis type="category" dataKey="code" tick={{ fontSize: 11 }} width={85} />
                  <Tooltip formatter={(v, n) => [`${Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} j`, n]} />
                  <Legend />
                  <Bar dataKey="Budget"        fill="#722ed1" barSize={8} />
                  <Bar dataKey="Chiff. édition" fill="#1677ff" barSize={8} />
                  <Bar dataKey="Consommé"     fill="#52c41a"  barSize={8} stackId="att" />
                  <Bar dataKey="RAF"          fill="#fa8c16"  barSize={8} stackId="att" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title={`Évolutions de la release (${evolutionsFiltrees.length})`}>
            <Table dataSource={evolutionsFiltrees} columns={colonnes} rowKey="code" size="small"
              scroll={{ x: 1200 }} pagination={{ pageSize: 20 }} />
          </Card>
        </>
      )}
    </div>
  )
}
