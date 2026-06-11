import React, { useState, useEffect } from 'react'
import { Card, Table, Select, Space, Typography, DatePicker } from 'antd'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { api } from '../api/client'

const { Title } = Typography

export default function DashboardAtterrissage() {
  const [data, setData] = useState(null)
  const [releases, setReleases] = useState([])
  const [equipes, setEquipes] = useState([])
  const [filtres, setFiltres] = useState({})
  const [date1, setDate1] = useState(dayjs())
  const [date2, setDate2] = useState(dayjs().subtract(30, 'day'))
  const navigate = useNavigate()

  const charger = (params = {}) => {
    const d1 = (params.date1 ?? date1)?.format('YYYY-MM-DD')
    const d2 = (params.date2 ?? date2)?.format('YYYY-MM-DD')
    const p = { ...filtres, ...params }
    if (d1) p.date1 = d1
    if (d2) p.date2 = d2
    api.getDashboardAtterrissage(p).then(setData)
  }

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

  const onDate1Change = (d) => {
    setDate1(d)
    charger({ date1: d })
  }

  const onDate2Change = (d) => {
    setDate2(d)
    charger({ date2: d })
  }

  const colonnes = [
    {
      title: '', key: 'couleur', width: 12,
      render: (_, r) => <div style={{ width: 8, height: 32, borderRadius: 4, background: r.couleur === 'rouge' ? '#f5222d' : r.couleur === 'orange' ? '#fa8c16' : '#52c41a' }} />
    },
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, render: v => <a onClick={() => navigate(`/evolutions/${v}`)}>{v}</a> },
    { title: 'Libellé', dataIndex: 'libelle', key: 'lib', ellipsis: true },
    { title: 'Équipe', dataIndex: 'equipe', key: 'eq', width: 110, render: v => equipes.find(e => e.code === v)?.libelle || v },
    { title: 'Release', dataIndex: 'release', key: 'rel', width: 160, ellipsis: true },
    {
      title: 'Atterrissage date 1 (j)', dataIndex: 'att_date1', key: 'a1', width: 155, align: 'right',
      render: (v, r) => v != null ? <span title={`Snapshot : ${r.snap1_date}`}>{v}</span> : '-'
    },
    {
      title: 'Atterrissage date 2 (j)', dataIndex: 'att_date2', key: 'a2', width: 155, align: 'right',
      render: (v, r) => v != null ? <span title={`Snapshot : ${r.snap2_date}`}>{v}</span> : '-'
    },
    {
      title: 'Δ Atterrissage (j)', dataIndex: 'delta', key: 'delta', width: 130, align: 'right',
      render: v => v == null ? '-' : <span style={{ color: v > 0 ? '#f5222d' : v < 0 ? '#52c41a' : undefined }}>{v > 0 ? `+${v}` : v}</span>
    },
  ]

  return (
    <div>
      <Title level={3}>Dashboard Atterrissage</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <DatePicker
          value={date1}
          onChange={onDate1Change}
          format="DD/MM/YYYY"
          placeholder="Date 1"
          style={{ width: 140 }}
        />
        <DatePicker
          value={date2}
          onChange={onDate2Change}
          format="DD/MM/YYYY"
          placeholder="Date 2"
          style={{ width: 140 }}
        />
        <Select placeholder="Release" style={{ width: 220 }} allowClear onChange={v => appliquer(v, 'release')}
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))} />
        <Select placeholder="Équipe" style={{ width: 180 }} allowClear onChange={v => appliquer(v, 'equipe')}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))} />
      </Space>

      <div style={{ display: 'flex', gap: 16, marginBottom: 12, alignItems: 'center' }}>
        <span><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: '#52c41a', marginRight: 6 }} />Stable ou amélioration</span>
        <span><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: '#fa8c16', marginRight: 6 }} />Dérive légère (&lt;5j)</span>
        <span><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: '#f5222d', marginRight: 6 }} />Dérive significative (&gt;5j)</span>
      </div>

      <Card>
        <Table
          dataSource={data?.evolutions || []}
          columns={colonnes}
          rowKey="code"
          size="small"
          scroll={{ x: 900 }}
          pagination={{ pageSize: 25 }}
          rowClassName={r => r.couleur === 'rouge' ? 'row-rouge' : r.couleur === 'orange' ? 'row-orange' : ''}
        />
      </Card>
    </div>
  )
}
