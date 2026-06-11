import React, { useState, useEffect, useMemo } from 'react'
import { Card, Select, Table, Tag, Row, Col, Typography, Space, Statistic, Collapse, InputNumber, message } from 'antd'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { MOIS_LABELS, formatMoisKey } from '../utils'

const { Title } = Typography
const COULEUR_STATUT = { 'À faire': '#d9d9d9', 'En cours': '#1677ff', 'Terminé': '#52c41a' }
const COULEURS_PIE = ['#d9d9d9', '#1677ff', '#52c41a', '#f5222d']

export default function DashboardEquipe() {
  const [equipes, setEquipes] = useState([])
  const [releases, setReleases] = useState([])
  const [equipeSelectionnee, setEquipeSelectionnee] = useState(null)
  const [data, setData] = useState(null)
  const [release, setRelease] = useState(null)
  const [rafEdits, setRafEdits] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    api.getEquipes().then(e => setEquipes(e.filter(eq => eq.type_equipe === 'DEV'))).catch(console.error)
    api.getReleases().then(setReleases).catch(console.error)
  }, [])

  const charger = (eq, rel) => {
    if (!eq) return
    const params = {}
    if (rel) params.release = rel
    api.getDashboardEquipe(eq, params).then(d => {
      setData(d)
      // Initialise les RAF depuis l'API
      const initRaf = {}
      ;(d.hors_evol_taches || []).forEach(t => { initRaf[t.key] = t.raf ?? 0 })
      setRafEdits(initRaf)
    }).catch(console.error)
  }

  const sauvegarderRaf = (row, valeur) => {
    api.updateRafHorsEvolution(row.time_niv2, row.nom_tache, valeur ?? 0)
      .then(() => {
        message.success('RAF enregistré')
        // Recharge pour mettre à jour les totaux
        charger(equipeSelectionnee, release)
      })
      .catch(() => message.error('Erreur lors de la sauvegarde'))
  }

  // Colonnes dynamiques pour la section hors évolutions
  const { allMois, colonnesHors } = useMemo(() => {
    const taches = data?.hors_evol_taches || []
    const moisSet = new Set()
    taches.forEach(t => Object.keys(t).forEach(k => {
      if (/^\d{4}-\d{2}$/.test(k)) moisSet.add(k)
    }))
    const allMois = [...moisSet].sort()
    const colonnesHors = [
      {
        title: 'Tâche',
        key: 'tache',
        ellipsis: true,
        render: (_, r) => (
          <div>
            <div style={{ fontWeight: 500 }}>{r.nom_tache || <span style={{ color: '#aaa' }}>—</span>}</div>
            <div style={{ color: '#888', fontSize: 11 }}>{r.time_niv2}</div>
          </div>
        ),
      },
      ...allMois.map(m => ({
        title: formatMoisKey(m),
        dataIndex: m,
        key: m,
        width: 75,
        align: 'right',
        render: v => v ? v.toFixed(2) : <span style={{ color: '#d9d9d9' }}>—</span>,
      })),
      {
        title: 'Total',
        dataIndex: 'total',
        key: 'total',
        width: 80,
        align: 'right',
        fixed: 'right',
        render: v => <strong>{(v || 0).toFixed(2)}</strong>,
      },
      {
        title: 'RAF (j)',
        key: 'raf',
        width: 100,
        align: 'right',
        fixed: 'right',
        render: (_, r) => (
          <InputNumber
            size="small"
            min={0}
            step={0.5}
            precision={2}
            value={rafEdits[r.key] ?? r.raf ?? 0}
            style={{ width: 80 }}
            onChange={val => setRafEdits(prev => ({ ...prev, [r.key]: val }))}
            onBlur={e => {
              const val = parseFloat(e.target.value.replace(',', '.')) || 0
              sauvegarderRaf(r, val)
            }}
            onPressEnter={e => {
              const val = parseFloat(e.target.value.replace(',', '.')) || 0
              sauvegarderRaf(r, val)
            }}
          />
        ),
      },
    ]
    return { allMois, colonnesHors }
  }, [data, rafEdits])

  // Colonnes évolutions
  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, render: v => <a onClick={() => navigate(`/evolutions/${v}`)}>{v}</a> },
    { title: 'Libellé', dataIndex: 'libelle', key: 'lib', ellipsis: true },
    { title: 'Statut Aha', dataIndex: 'statut_aha', key: 'st', width: 100, render: v => <Tag>{v}</Tag> },
    { title: 'Budget Aha (j)', dataIndex: 'budget', key: 'budget', width: 105, align: 'right', render: v => v ?? '-' },
    { title: 'Macro (j)', dataIndex: 'macro_chiffrage', key: 'mc', width: 90, align: 'right', render: v => v ?? '-' },
    { title: 'Chiff. éd. (j)', dataIndex: 'chiffrage_edition', key: 'ce', width: 95, align: 'right', render: v => v ?? '-' },
    { title: 'Tps DEV (j)', dataIndex: 'temps_dev', key: 'td', width: 100, align: 'right' },
    { title: 'Tps Testing (j)', dataIndex: 'temps_testing', key: 'tt', width: 110, align: 'right' },
    { title: 'RAF DEV (j)', dataIndex: 'raf_dev', key: 'raf', width: 100, align: 'right' },
    { title: 'RAF Testing (j)', dataIndex: 'raf_testing', key: 'rft', width: 110, align: 'right', render: v => v ?? '-' },
    {
      title: 'Atterrissage (j)', key: 'att', width: 120, align: 'right',
      render: (_, r) => {
        const val = (r.conso_2025 || 0) + (r.temps_dev || 0) + (r.temps_testing || 0) + (r.raf_dev || 0) + (r.raf_testing || 0)
        return <strong style={{ color: '#1677ff' }}>{val.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
      }
    },
    ...['Recette interne', 'Livraison intégration', 'Recette Pôle Testing'].map(e => ({
      title: e.replace('Recette Pôle Testing', 'Rec. PT').replace('Livraison intégration', 'Livraison'),
      key: e, width: 90,
      render: (_, r) => {
        const s = r.etapes?.[e]
        return s ? <Tag color={COULEUR_STATUT[s]}>{s}</Tag> : '-'
      }
    })),
  ]

  const donneesRecette = data ? Object.entries(data.recette_interne).map(([s, n]) => ({ name: s, value: n })) : []

  const tempsDevTotal = data ? data.evolutions.reduce((acc, e) => acc + (e.temps_dev || 0) + (e.temps_testing || 0), 0).toFixed(2) : 0
  const budgetTotal = data ? data.evolutions.reduce((acc, e) => acc + (e.budget || 0), 0).toFixed(2) : 0
  const macroTotal = data ? data.evolutions.reduce((acc, e) => acc + (e.macro_chiffrage || 0), 0).toFixed(2) : 0
  const chiffrageEdTotal = data ? data.evolutions.reduce((acc, e) => acc + (e.chiffrage_edition || 0), 0).toFixed(2) : 0

  return (
    <div>
      <Title level={3}>Dashboard par équipe</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select placeholder="Choisir une équipe" style={{ width: 200 }}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))}
          onChange={v => { setEquipeSelectionnee(v); charger(v, release) }} />
        <Select placeholder="Release" style={{ width: 220 }} allowClear
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))}
          onChange={v => { setRelease(v); charger(equipeSelectionnee, v) }} />
      </Space>

      {data && (
        <>
          {/* Statistiques synthèse */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}>
              <Card>
                <Statistic title="Évolutions" value={data.evolutions.length} />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic title="Budget Aha (j)" value={budgetTotal} precision={2} />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic title="Macro chiffrage (j)" value={macroTotal} precision={2} />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic title="Chiffrage édition (j)" value={chiffrageEdTotal} precision={2} />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic title="Tps consommé DEV + Testing (j)" value={tempsDevTotal} precision={2} />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="Tps hors évolutions (j)"
                  value={data.hors_evol_total ?? 0}
                  precision={2}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="RAF évolutions (j)"
                  value={data.evol_raf_total ?? 0}
                  precision={2}
                  valueStyle={{ color: '#1677ff' }}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card>
                <Statistic
                  title="RAF total (évol + hors) (j)"
                  value={data.raf_global_total ?? 0}
                  precision={2}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Graphiques */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Card title="Avancement recette interne">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={donneesRecette} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}
                      label={({ name, value }) => value > 0 ? `${name}: ${value}` : ''}>
                      {donneesRecette.map((_, i) => <Cell key={i} fill={COULEURS_PIE[i % 4]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={16}>
              <Card title="Temps DEV vs Macro chiffrage par évolution (j)">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={(data.evolutions || []).slice(0, 15).map(e => ({
                    code: e.code,
                    'Temps DEV': e.temps_dev,
                    'Macro': e.macro_chiffrage || 0,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="code" tick={{ fontSize: 10 }} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Temps DEV" fill="#1677ff" />
                    <Bar dataKey="Macro" fill="#d9d9d9" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* Tableau évolutions */}
          <Card title={`Évolutions (${data.evolutions?.length || 0})`} style={{ marginBottom: 16 }}>
            <Table dataSource={data.evolutions} columns={colonnes} rowKey="code" size="small"
              scroll={{ x: 1400 }} pagination={{ pageSize: 20 }} />
          </Card>

          {/* Section hors évolutions */}
          {data.hors_evol_taches?.length > 0 && (
            <Collapse
              items={[{
                key: 'hors',
                label: (
                  <span>
                    Temps hors évolutions —&nbsp;
                    <strong style={{ color: '#fa8c16' }}>{data.hors_evol_total} j</strong>
                    &nbsp;sur {data.hors_evol_taches.length} tâche{data.hors_evol_taches.length > 1 ? 's' : ''}
                    {data.hors_evol_raf_total > 0 && (
                      <>&nbsp;— RAF :&nbsp;<strong style={{ color: '#722ed1' }}>{data.hors_evol_raf_total} j</strong></>
                    )}
                  </span>
                ),
                children: (
                  <Table
                    dataSource={data.hors_evol_taches}
                    columns={colonnesHors}
                    rowKey="key"
                    size="small"
                    pagination={false}
                    scroll={{ x: 'max-content' }}
                  />
                ),
              }]}
            />
          )}
        </>
      )}
    </div>
  )
}
