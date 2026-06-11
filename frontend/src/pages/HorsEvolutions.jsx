import React, { useState, useEffect, useMemo } from 'react'
import { Card, Table, Select, Space, Typography, InputNumber, message } from 'antd'
import { api } from '../api/client'
import { MOIS_LABELS, formatMoisKey } from '../utils'

const { Title, Text } = Typography

/** Extrait les clés de mois depuis le tableau pré-pivoté renvoyé par l'API */
function getMoisFromTableau(tableau) {
  const moisSet = new Set()
  ;(tableau || []).forEach(r =>
    Object.keys(r).forEach(k => { if (/^\d{4}-\d{2}$/.test(k)) moisSet.add(k) })
  )
  return [...moisSet].sort()
}

/** Construit les lignes collaborateurs pour une ligne expanded */
function buildCollabPivot(collabsByMonth) {
  const collabMap = {}
  Object.entries(collabsByMonth || {}).forEach(([moisKey, collabs]) => {
    collabs.forEach(c => {
      if (!collabMap[c.matricule]) {
        collabMap[c.matricule] = { key: c.matricule, nom: c.nom, matricule: c.matricule, total: 0 }
      }
      const prev = collabMap[c.matricule][moisKey] || 0
      collabMap[c.matricule][moisKey] = Math.round((prev + c.jours) * 100) / 100
      collabMap[c.matricule].total = Math.round((collabMap[c.matricule].total + c.jours) * 100) / 100
    })
  })
  return Object.values(collabMap)
}

const cellJours = v => v ? v.toFixed(2) : <span style={{ color: '#d9d9d9' }}>—</span>

export default function HorsEvolutions() {
  const [data, setData] = useState(null)
  const [filtres, setFiltres] = useState({})
  const [expanded, setExpanded] = useState([])
  const [equipes, setEquipes] = useState([])
  const [rafEdits, setRafEdits] = useState({})
  const [pageSize, setPageSize] = useState(30)

  const charger = (params = {}) => {
    setExpanded([])
    api.getHorsEvolutions(params).then(d => {
      setData(d)
      // Initialise les valeurs RAF depuis l'API
      const initRaf = {}
      ;(d.tableau || []).forEach(r => { initRaf[r.key] = r.raf ?? 0 })
      setRafEdits(initRaf)
    }).catch(console.error)
  }

  useEffect(() => {
    charger()
    api.getEquipes().then(setEquipes).catch(console.error)
  }, [])

  const appliquer = (val, cle) => {
    const f = { ...filtres, [cle]: val ?? undefined }
    const fPropres = Object.fromEntries(Object.entries(f).filter(([, v]) => v != null))
    setFiltres(fPropres)
    charger(fPropres)
  }

  const sauvegarderRaf = (row, valeur) => {
    api.updateRafHorsEvolution(row.time_niv2, row.nom_tache, valeur ?? 0)
      .then(() => message.success('RAF enregistré'))
      .catch(() => message.error('Erreur lors de la sauvegarde'))
  }

  const taskRows = data?.tableau || []
  const allMois = useMemo(() => getMoisFromTableau(taskRows), [taskRows])

  // Colonnes du tableau principal
  const colonnesTaches = useMemo(() => [
    {
      title: 'Tâche',
      key: 'tache',
      ellipsis: false,
      width: 280,
      render: (_, r) => (
        <div>
          <div style={{ fontWeight: 500 }}>{r.nom_tache || <span style={{ color: '#aaa' }}>Sans nom</span>}</div>
          <div style={{ color: '#888', fontSize: 11 }}>{r.time_niv2}</div>
        </div>
      ),
    },
    ...allMois.map(m => ({
      title: formatMoisKey(m),
      dataIndex: m,
      key: m,
      width: 80,
      align: 'right',
      render: cellJours,
    })),
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 80,
      align: 'right',
      render: v => <strong>{(v || 0).toFixed(2)}</strong>,
      fixed: 'right',
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
  ], [allMois, rafEdits])

  // Colonnes du tableau collaborateurs (expanded)
  const colonnesCollabs = useMemo(() => [
    { title: 'Collaborateur', key: 'nom', dataIndex: 'nom', width: 220 },
    { title: 'Matricule', key: 'mat', dataIndex: 'matricule', width: 110 },
    ...allMois.map(m => ({
      title: formatMoisKey(m),
      dataIndex: m,
      key: m,
      width: 80,
      align: 'right',
      render: cellJours,
    })),
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 80,
      align: 'right',
      render: v => <strong>{(v || 0).toFixed(2)}</strong>,
    },
  ], [allMois])

  const hasCollabs = row => Object.values(row.collabsByMonth || {}).some(c => c.length > 0)

  const rafTotal = Object.values(rafEdits).reduce((s, v) => s + (v || 0), 0)

  return (
    <div>
      <Title level={3}>Activité hors évolutions (03-Edition)</Title>

      <Space wrap style={{ marginBottom: 16 }}>
        <InputNumber
          placeholder="Année"
          style={{ width: 100 }}
          onChange={v => appliquer(v, 'annee')}
          min={2020} max={2030}
        />
        <Select
          placeholder="Mois"
          style={{ width: 120 }}
          allowClear
          onChange={v => appliquer(v, 'mois')}
          options={MOIS_LABELS.map((m, i) => ({ value: i + 1, label: m }))}
        />
        <Select
          placeholder="Équipe"
          style={{ width: 180 }}
          allowClear
          onChange={v => appliquer(v, 'equipe')}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))}
        />
        {taskRows.length > 0 && (
          <Text type="secondary">
            {taskRows.length} tâche{taskRows.length > 1 ? 's' : ''}
            {rafTotal > 0 && <> — RAF total : <strong>{rafTotal.toFixed(2)} j</strong></>}
          </Text>
        )}
      </Space>

      <Card>
        <Table
          dataSource={taskRows}
          columns={colonnesTaches}
          rowKey="key"
          size="small"
          pagination={{
            pageSize,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '30', '50', '100'],
            onShowSizeChange: (_, size) => setPageSize(size),
          }}
          scroll={{ x: 'max-content' }}
          expandable={{
            expandedRowKeys: expanded,
            onExpand: (open, record) =>
              setExpanded(open ? [...expanded, record.key] : expanded.filter(k => k !== record.key)),
            expandedRowRender: (record) => {
              const collabRows = buildCollabPivot(record.collabsByMonth)
              return (
                <div style={{ margin: '8px 0 8px 48px' }}>
                  <Table
                    dataSource={collabRows}
                    columns={colonnesCollabs}
                    rowKey="key"
                    size="small"
                    pagination={false}
                    scroll={{ x: 'max-content' }}
                  />
                </div>
              )
            },
            rowExpandable: hasCollabs,
          }}
        />
      </Card>
    </div>
  )
}
