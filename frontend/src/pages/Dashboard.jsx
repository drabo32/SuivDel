import React, { useState, useEffect, useMemo } from 'react'
import {
  Card, Select, Table, Tag, Row, Col, Typography, Space,
  Statistic, InputNumber, message, Input,
} from 'antd'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { MOIS_LABELS, formatJ, formatMoisKey } from '../utils'

const { Title } = Typography

const COULEUR_STATUT = { 'À faire': '#d9d9d9', 'En cours': '#1677ff', 'Terminé': '#52c41a' }
const COULEURS_PIE = ['#d9d9d9', '#1677ff', '#52c41a']

function TooltipBudget({ active, payload, label, libelleMap }) {
  if (!active || !payload?.length) return null
  const libelle = libelleMap?.[label] || ''
  const titre = libelle ? `${label} — ${libelle}` : label
  return (
    <div style={{ background: '#fff', border: '1px solid #d9d9d9', padding: '8px 12px', borderRadius: 4, fontSize: 12 }}>
      <p style={{ margin: '0 0 6px', fontWeight: 600 }}>{titre}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ margin: '2px 0', color: p.fill }}>
          {p.name} : {Number(p.value).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} j
        </p>
      ))}
    </div>
  )
}

function BarreStatuts({ data, titre }) {
  const donneesChart = Object.entries(data).map(([eq, v]) => ({ equipe: eq, ...v }))
  if (!donneesChart.length) return null
  return (
    <Card title={titre} size="small">
      <ResponsiveContainer width="100%" height={200}>
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

export default function Dashboard() {
  const [equipes, setEquipes] = useState([])
  const [releases, setReleases] = useState([])
  const [equipeSelectionnee, setEquipeSelectionnee] = useState(null)
  const [releaseSelectionnee, setReleaseSelectionnee] = useState(null)
  const [data, setData] = useState(null)
  const [rafEdits, setRafEdits] = useState({})
  const [filtreCode, setFiltreCode] = useState('')
  const [filtreStatutAha, setFiltreStatutAha] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.getEquipes().then(e => setEquipes(e.filter(eq => eq.type_equipe === 'DEV'))).catch(console.error)
    api.getReleases().then(setReleases).catch(console.error)
    charger(null, null)
  }, [])

  const charger = (eq, rel) => {
    const params = {}
    if (eq) params.equipe = eq
    if (rel) params.release = rel
    api.getDashboardPrincipal(params).then(d => {
      setData(d)
      const initRaf = {}
      ;(d.hors_evol_taches || []).forEach(t => { initRaf[t.key] = t.raf ?? 0 })
      setRafEdits(initRaf)
    }).catch(console.error)
  }

  const sauvegarderRaf = (row, valeur) => {
    api.updateRafHorsEvolution(row.time_niv2, row.nom_tache, valeur ?? 0)
      .then(() => { message.success('RAF enregistré'); charger(equipeSelectionnee, releaseSelectionnee) })
      .catch(() => message.error('Erreur lors de la sauvegarde'))
  }

  // Colonnes hors-évolutions dynamiques
  const { allMois, colonnesHors } = useMemo(() => {
    const taches = data?.hors_evol_taches || []
    const moisSet = new Set()
    taches.forEach(t => Object.keys(t).forEach(k => { if (/^\d{4}-\d{2}$/.test(k)) moisSet.add(k) }))
    const allMois = [...moisSet].sort()
    const colonnesHors = [
      {
        title: 'Tâche', key: 'tache', ellipsis: true,
        render: (_, r) => (
          <div>
            <div style={{ fontWeight: 500 }}>{r.nom_tache || <span style={{ color: '#aaa' }}>—</span>}</div>
            <div style={{ color: '#888', fontSize: 11 }}>{r.time_niv2}</div>
          </div>
        ),
      },
      ...allMois.map(m => ({
        title: formatMoisKey(m), dataIndex: m, key: m, width: 75, align: 'right',
        render: v => v ? v.toFixed(2) : <span style={{ color: '#d9d9d9' }}>—</span>,
      })),
      { title: 'Total', dataIndex: 'total', key: 'total', width: 80, align: 'right', fixed: 'right', render: v => <strong>{(v || 0).toFixed(2)}</strong> },
      {
        title: 'RAF (j)', key: 'raf', width: 100, align: 'right', fixed: 'right',
        render: (_, r) => (
          <InputNumber size="small" min={0} step={0.5} precision={2}
            value={rafEdits[r.key] ?? r.raf ?? 0} style={{ width: 80 }}
            onChange={val => setRafEdits(prev => ({ ...prev, [r.key]: val }))}
            onBlur={e => { const val = parseFloat(e.target.value.replace(',', '.')) || 0; sauvegarderRaf(r, val) }}
            onPressEnter={e => { const val = parseFloat(e.target.value.replace(',', '.')) || 0; sauvegarderRaf(r, val) }}
          />
        ),
      },
    ]
    return { allMois, colonnesHors }
  }, [data, rafEdits])

  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, render: v => <a onClick={() => navigate(`/evolutions/${v}`)}>{v}</a> },
    { title: 'Libellé', dataIndex: 'libelle', key: 'lib', ellipsis: true },
    { title: 'Équipe', dataIndex: 'equipe', key: 'eq', width: 90 },
    { title: 'Release', dataIndex: 'release', key: 'rel', width: 80 },
    { title: 'Statut Aha', dataIndex: 'statut_aha', key: 'st', width: 100, render: v => <Tag>{v}</Tag> },
    { title: 'Budget (j)', dataIndex: 'budget', key: 'budget', width: 90, align: 'right', render: formatJ },
    { title: 'Macro (j)', dataIndex: 'macro_chiffrage', key: 'mc', width: 85, align: 'right', render: formatJ },
    { title: 'Chiff. éd. (j)', dataIndex: 'chiffrage_edition', key: 'ce', width: 95, align: 'right', render: formatJ },
    { title: 'Tps DEV (j)', dataIndex: 'temps_dev', key: 'td', width: 95, align: 'right', render: formatJ },
    { title: 'Tps Testing (j)', dataIndex: 'temps_testing', key: 'tt', width: 110, align: 'right', render: formatJ },
    { title: 'RAF DEV (j)', dataIndex: 'raf_dev', key: 'rd', width: 95, align: 'right', render: formatJ },
    { title: 'RAF Testing (j)', dataIndex: 'raf_testing', key: 'rft', width: 110, align: 'right', render: formatJ },
    {
      title: 'Atterrissage (j)', key: 'att', width: 120, align: 'right',
      render: (_, r) => <strong style={{ color: '#1677ff' }}>{formatJ(r.atterrissage)}</strong>
    },
    {
      title: 'Δ vs M-1 (j)', key: 'delta', width: 105, align: 'right',
      render: (_, r) => {
        const d = r.delta_atterrissage
        if (d == null) return <span style={{ color: '#bbb' }}>—</span>
        if (d === 0) return <span style={{ color: '#888' }}>= 0</span>
        const couleur = d > 0 ? '#f5222d' : '#52c41a'
        return <strong style={{ color: couleur }}>{d > 0 ? `+${formatJ(d)}` : formatJ(d)}</strong>
      }
    },
    { title: 'Avanc.', dataIndex: 'avancement_moyen', key: 'av', width: 70, align: 'right', render: v => `${v}%` },
    ...['Recette interne', 'Livraison intégration', 'Recette Pôle Testing'].map(e => ({
      title: e.replace('Recette Pôle Testing', 'Rec. PT').replace('Livraison intégration', 'Livraison'),
      key: e, width: 85,
      render: (_, r) => {
        const s = r.etapes?.[e]
        return s ? <Tag color={COULEUR_STATUT[s]} style={{ fontSize: 11 }}>{s}</Tag> : '-'
      }
    })),
  ]

  const evolutions = useMemo(() => {
    let list = data?.evolutions || []
    if (filtreCode) list = list.filter(e => e.code.toLowerCase().includes(filtreCode.toLowerCase()))
    if (filtreStatutAha) list = list.filter(e => e.statut_aha === filtreStatutAha)
    return list
  }, [data, filtreCode, filtreStatutAha])

  const optionsStatutAha = useMemo(() => {
    const vals = [...new Set((data?.evolutions || []).map(e => e.statut_aha).filter(Boolean))].sort()
    return vals.map(v => ({ value: v, label: v }))
  }, [data])

  const totalBudget = evolutions.reduce((a, e) => a + (e.budget || 0), 0)
  const totalChiffrageEd = evolutions.reduce((a, e) => a + (e.chiffrage_edition || 0), 0)
  const totalConsomme = evolutions.reduce((a, e) => a + (e.consomme_total || 0), 0)
  const totalAtterrissage = evolutions.reduce((a, e) => a + (e.atterrissage || 0), 0)
  const totalRafEvol = evolutions.reduce((a, e) => a + (e.raf_total || 0), 0)
  const totalRafGlobal = totalRafEvol + (data?.hors_evol_raf_total || 0)

  const libelleMap = useMemo(
    () => Object.fromEntries(evolutions.map(e => [e.code, e.libelle || ''])),
    [evolutions]
  )

  const donneesChart = evolutions.map(e => ({
    code: e.code,
    'Budget': e.budget || 0,
    'Chiff. édition': e.chiffrage_edition || 0,
    'Consommé': e.consomme_total || 0,
    'RAF': e.raf_total || 0,
  }))
  const chartHeight = Math.max(300, evolutions.length * 28)

  const donneesPie = data
    ? Object.entries(data.recette_interne ?? {}).filter(([, v]) => v > 0).map(([n, v]) => ({ name: n, value: v }))
    : []

  return (
    <div>
      <Title level={3}>Dashboard</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select placeholder="Équipe" style={{ width: 200 }} allowClear
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))}
          onChange={v => { setEquipeSelectionnee(v || null); charger(v || null, releaseSelectionnee) }} />
        <Select placeholder="Release" style={{ width: 240 }} allowClear
          options={[
            { value: 'HORS_RELEASE', label: '— Hors release —' },
            ...releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` })),
          ]}
          onChange={v => { setReleaseSelectionnee(v || null); charger(equipeSelectionnee, v || null) }} />
      </Space>

      {data && (
        <>
          {/* Stats synthèse */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}><Card><Statistic title="Évolutions" value={evolutions.length} /></Card></Col>
            <Col span={4}><Card><Statistic title="Budget Aha (j)" value={formatJ(totalBudget)} /></Card></Col>
            <Col span={4}><Card><Statistic title="Chiffrage édition (j)" value={formatJ(totalChiffrageEd)} /></Card></Col>
            <Col span={4}><Card><Statistic title="Consommé total (j)" value={formatJ(totalConsomme)} /></Card></Col>
            <Col span={4}><Card><Statistic title="Atterrissage total (j)" value={formatJ(totalAtterrissage)} valueStyle={{ color: '#1677ff' }} /></Card></Col>
            <Col span={4}><Card><Statistic title="RAF total (évol + hors) (j)" value={formatJ(totalRafGlobal)} valueStyle={{ color: '#fa8c16' }} /></Card></Col>
          </Row>

          {/* Graphiques synthèse */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card title="Recette interne" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={donneesPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, value }) => `${name}: ${value}`}>
                      {donneesPie.map((entry, i) => <Cell key={i} fill={COULEUR_STATUT[entry.name] || COULEURS_PIE[i]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={9}>
              <BarreStatuts data={data.par_equipe_livraison} titre="Livraison intégration par équipe" />
            </Col>
            <Col span={9}>
              <BarreStatuts data={data.par_equipe_testing} titre="Recette Pôle Testing par équipe" />
            </Col>
          </Row>

          {/* Graphique par évolution */}
          <Card title={`Budget / Atterrissage par évolution (${evolutions.length})`} style={{ marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <BarChart data={donneesChart} layout="vertical" margin={{ left: 90, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tick={{ fontSize: 11 }} unit=" j" />
                <YAxis type="category" dataKey="code" tick={{ fontSize: 11 }} width={85} />
                <Tooltip content={(props) => <TooltipBudget {...props} libelleMap={libelleMap} />} />
                <Legend />
                <Bar dataKey="Budget" fill="#722ed1" barSize={7} />
                <Bar dataKey="Chiff. édition" fill="#1677ff" barSize={7} />
                <Bar dataKey="Consommé" fill="#52c41a" barSize={7} stackId="att" />
                <Bar dataKey="RAF" fill="#fa8c16" barSize={7} stackId="att" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Tableau évolutions */}
          <Card
            title={`Évolutions (${evolutions.length})`}
            style={{ marginBottom: 16 }}
            extra={
              <Space>
                <Input.Search
                  placeholder="Code évolution"
                  allowClear
                  style={{ width: 180 }}
                  onChange={e => setFiltreCode(e.target.value)}
                  onSearch={v => setFiltreCode(v)}
                />
                <Select
                  placeholder="Statut Aha"
                  style={{ width: 180 }}
                  allowClear
                  options={optionsStatutAha}
                  onChange={v => setFiltreStatutAha(v || null)}
                />
              </Space>
            }
          >
            <Table dataSource={evolutions} columns={colonnes} rowKey="code" size="small"
              scroll={{ x: 1400 }} pagination={{ pageSize: 25 }}
              summary={() => {
                const s = evolutions
                const tot = f => formatJ(s.reduce((a, e) => a + (e[f] || 0), 0))
                const totalAtt = s.reduce((a, e) => a + (e.atterrissage || 0), 0)
                return (
                  <Table.Summary.Row style={{ background: '#fafafa', fontWeight: 600 }}>
                    <Table.Summary.Cell index={0} colSpan={5}>Total ({s.length})</Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right">{tot('budget')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={2} align="right">{tot('macro_chiffrage')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={3} align="right">{tot('chiffrage_edition')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={4} align="right">{tot('temps_dev')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={5} align="right">{tot('temps_testing')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={6} align="right">{tot('raf_dev')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={7} align="right">{tot('raf_testing')}</Table.Summary.Cell>
                    <Table.Summary.Cell index={8} align="right" style={{ color: '#1677ff' }}>{formatJ(totalAtt)}</Table.Summary.Cell>
                    <Table.Summary.Cell index={9} colSpan={5} />
                  </Table.Summary.Row>
                )
              }}
            />
          </Card>

          {/* Hors-évolutions (seulement si équipe sélectionnée) */}
          {equipeSelectionnee && (
            <Card title={`Hors-évolutions — Tps consommé (j) · Total : ${formatJ(data.hors_evol_total)} · RAF : ${formatJ(data.hors_evol_raf_total)}`}>
              <Table dataSource={data.hors_evol_taches} columns={colonnesHors} rowKey="key"
                size="small" scroll={{ x: 'max-content' }} pagination={false} />
            </Card>
          )}
        </>
      )}
    </div>
  )
}
