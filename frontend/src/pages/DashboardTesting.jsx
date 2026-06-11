import React, { useState, useEffect, useMemo } from 'react'
import { Card, Table, Tag, Row, Col, Statistic, Select, Space, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { api } from '../api/client'

const { Title } = Typography

const formatJ = v => (v || 0).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function DashboardTesting() {
  const [data, setData] = useState(null)
  const [releases, setReleases] = useState([])
  const [equipes, setEquipes] = useState([])
  const [filtreEquipe, setFiltreEquipe] = useState(null)
  const [filtreResponsable, setFiltreResponsable] = useState(null)
  const [filtreLivree, setFiltreLivree] = useState(null) // 'oui' | 'non' | null
  const navigate = useNavigate()

  const charger = (params = {}) => api.getDashboardTesting(params).then(setData)

  useEffect(() => {
    charger()
    api.getReleases().then(setReleases)
    api.getEquipes().then(e => setEquipes(e.filter(eq => eq.type_equipe === 'DEV')))
  }, [])

  const lignesFiltrees = useMemo(() => {
    if (!data) return []
    return data.evolutions_testing.filter(r => {
      if (filtreEquipe && r.equipe !== filtreEquipe) return false
      if (filtreResponsable && r.responsable !== filtreResponsable) return false
      if (filtreLivree === 'oui' && !r.date_livr_reelle) return false
      if (filtreLivree === 'non' && r.date_livr_reelle) return false
      return true
    })
  }, [data, filtreEquipe, filtreResponsable, filtreLivree])

  const optionsResponsables = useMemo(() => {
    if (!data) return []
    const vals = [...new Set(data.evolutions_testing.map(r => r.responsable).filter(Boolean))].sort()
    return vals.map(v => ({ value: v, label: v }))
  }, [data])

  const totalRaf = lignesFiltrees.reduce((acc, r) => acc + (r.raf_testing || 0), 0)
  const totalTemps = lignesFiltrees.reduce((acc, r) => acc + (r.temps_testing || 0), 0)

  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120, render: v => <a onClick={() => navigate(`/evolutions/${v}`)}>{v}</a> },
    { title: 'Libellé', dataIndex: 'libelle', key: 'lib', ellipsis: true },
    { title: 'Équipe', dataIndex: 'equipe', key: 'eq', width: 110 },
    { title: 'Responsable', dataIndex: 'responsable', key: 'resp', width: 140, render: v => v || '-' },
    {
      title: 'Statut recette', dataIndex: 'statut_recette', key: 'sr', width: 120,
      render: v => <Tag color={v === 'En cours' ? 'blue' : 'default'}>{v}</Tag>
    },
    { title: 'Avancement', dataIndex: 'avancement', key: 'av', width: 95, align: 'right', render: v => `${v}%` },
    {
      title: 'Date prév. livraison', dataIndex: 'date_livr_prevue', key: 'dlp', width: 145,
      render: v => v ? dayjs(v).format('DD/MM/YYYY') : '-'
    },
    {
      title: 'Date réelle livraison', dataIndex: 'date_livr_reelle', key: 'dlr', width: 145,
      render: v => v
        ? <Tag color="green">{dayjs(v).format('DD/MM/YYYY')}</Tag>
        : <Tag color="default">Non livrée</Tag>
    },
    { title: 'Tps Testing (j)', dataIndex: 'temps_testing', key: 'tt', width: 120, align: 'right', render: v => formatJ(v || 0) },
    { title: 'RAF Testing (j)', dataIndex: 'raf_testing', key: 'raf', width: 120, align: 'right', render: v => v != null ? formatJ(v) : '-' },
  ]

  return (
    <div>
      <Title level={3}>Dashboard Pôle Testing</Title>
      <Space wrap style={{ marginBottom: 16 }}>
        <Select placeholder="Release" style={{ width: 220 }} allowClear
          options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))}
          onChange={v => charger(v ? { release: v } : {})} />
        <Select placeholder="Équipe" style={{ width: 180 }} allowClear
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))}
          onChange={v => setFiltreEquipe(v || null)} />
        <Select placeholder="Responsable" style={{ width: 200 }} allowClear
          options={optionsResponsables}
          onChange={v => setFiltreResponsable(v || null)} />
        <Select placeholder="Livraison intégration" style={{ width: 200 }} allowClear
          options={[
            { value: 'oui', label: 'Livrée (date réelle renseignée)' },
            { value: 'non', label: 'Non livrée' },
          ]}
          onChange={v => setFiltreLivree(v || null)} />
      </Space>

      {data && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card><Statistic title="Évolutions en recette (filtrées)" value={lignesFiltrees.length} valueStyle={{ color: '#1677ff' }} /></Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Total" value={data.nb_total} /></Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Σ RAF Testing (j)" value={formatJ(totalRaf)} valueStyle={{ color: '#cf1322' }} /></Card>
            </Col>
            <Col span={6}>
              <Card><Statistic title="Σ Tps Testing consommé (j)" value={formatJ(totalTemps)} /></Card>
            </Col>
          </Row>

          <Card title="Liste des évolutions">
            <Table
              dataSource={lignesFiltrees}
              columns={colonnes}
              rowKey="code"
              size="small"
              scroll={{ x: 1200 }}
              pagination={{ pageSize: 20 }}
              summary={() => (
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={8}><strong>Total</strong></Table.Summary.Cell>
                  <Table.Summary.Cell index={1} align="right"><strong>{formatJ(totalTemps)}</strong></Table.Summary.Cell>
                  <Table.Summary.Cell index={2} align="right"><strong>{formatJ(totalRaf)}</strong></Table.Summary.Cell>
                </Table.Summary.Row>
              )}
            />
          </Card>
        </>
      )}
    </div>
  )
}
