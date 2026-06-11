import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card, Descriptions, Form, InputNumber, DatePicker, Button, Table, Tag, Select,
  Typography, Space, Statistic, Row, Col, Collapse, message, Tabs, Input, Modal, Divider, Popconfirm
} from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'
import dayjs from 'dayjs'
import { api } from '../api/client'
import { DeleteOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const ETAPES = ['Analyse PM', 'Analyse PO', 'Analyse PPO', 'Développement', 'Recette interne', 'Livraison intégration', 'Recette Pôle Testing']
const COULEUR_STATUT = { 'À faire': 'default', 'En cours': 'blue', 'Terminé': 'green' }
const MOIS_FR = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
const formatJours = v => v == null ? '-' : Number(v).toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function SectionChiffrages({ evolution, onSaved }) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    form.setFieldsValue({
      macro_chiffrage: evolution.macro_chiffrage,
      chiffrage_edition: evolution.chiffrage_edition,
      raf_dev: evolution.raf_dev,
      raf_testing: evolution.raf_testing,
      date_fin_estimee: evolution.date_fin_estimee ? dayjs(evolution.date_fin_estimee) : null,
    })
  }, [evolution])

  const sauvegarder = async () => {
    const values = await form.validateFields()
    setLoading(true)
    try {
      await api.updateEvolution(evolution.code, {
        ...values,
        date_fin_estimee: values.date_fin_estimee ? values.date_fin_estimee.format('YYYY-MM-DD') : null,
        version_verrou: evolution.version_verrou,
      })
      message.success('Chiffrages sauvegardés')
      onSaved()
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Form form={form} layout="inline">
      <Form.Item name="macro_chiffrage" label="Macro chiffrage (j)">
        <InputNumber min={0} step={0.5} style={{ width: 120 }} />
      </Form.Item>
      <Form.Item name="chiffrage_edition" label="Chiffrage édition (j)">
        <InputNumber min={0} step={0.5} style={{ width: 120 }} />
      </Form.Item>
      <Form.Item name="raf_dev" label="RAF DEV (j)">
        <InputNumber min={0} step={0.5} style={{ width: 100 }} />
      </Form.Item>
      <Form.Item name="raf_testing" label="RAF Testing (j)">
        <InputNumber min={0} step={0.5} style={{ width: 100 }} />
      </Form.Item>
      <Form.Item name="date_fin_estimee" label="Date fin estimée">
        <DatePicker format="DD/MM/YYYY" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={sauvegarder}>Sauvegarder</Button>
      </Form.Item>
    </Form>
  )
}

function SectionEtapes({ etapes: etapesRaw, onSaved }) {
  const etapes = [...etapesRaw].sort((a, b) => ETAPES.indexOf(a.etape) - ETAPES.indexOf(b.etape))
  const [editId, setEditId] = useState(null)
  const [form] = Form.useForm()

  const editer = (etape) => {
    setEditId(etape.id)
    form.setFieldsValue({
      statut: etape.statut,
      pourcentage_avancement: etape.pourcentage_avancement,
      date_prevue: etape.date_prevue ? dayjs(etape.date_prevue) : null,
      date_reelle: etape.date_reelle ? dayjs(etape.date_reelle) : null,
      responsable: etape.responsable,
      commentaire: etape.commentaire,
      modifie_par: etape.modifie_par,
    })
  }

  const sauvegarder = async (etape) => {
    const values = await form.validateFields()
    try {
      await api.updateEtape(etape.id, {
        ...values,
        date_prevue: values.date_prevue ? values.date_prevue.format('YYYY-MM-DD') : null,
        date_reelle: values.date_reelle ? values.date_reelle.format('YYYY-MM-DD') : null,
        version_verrou: etape.version_verrou,
      })
      message.success('Étape sauvegardée')
      setEditId(null)
      onSaved()
    } catch (e) {
      message.error(e.message)
    }
  }

  const colonnes = [
    { title: 'Étape', dataIndex: 'etape', key: 'etape', width: 200 },
    { title: 'Statut', dataIndex: 'statut', key: 'statut', width: 110, render: v => <Tag color={COULEUR_STATUT[v]}>{v}</Tag> },
    { title: 'Avanc.', dataIndex: 'pourcentage_avancement', key: 'av', width: 70, render: (v, r) => r.etape === 'Livraison intégration' ? '-' : `${v}%` },
    { title: 'Date prévue', dataIndex: 'date_prevue', key: 'dp', width: 110, render: v => v ? dayjs(v).format('DD/MM/YYYY') : '-' },
    { title: 'Date réelle', dataIndex: 'date_reelle', key: 'dr', width: 110, render: v => v ? dayjs(v).format('DD/MM/YYYY') : '-' },
    { title: 'Responsable', dataIndex: 'responsable', key: 'resp', width: 140 },
    { title: 'Commentaire', dataIndex: 'commentaire', key: 'com', ellipsis: true },
    {
      title: '', key: 'action', width: 80,
      render: (_, r) => editId === r.id
        ? <Button size="small" type="primary" onClick={() => sauvegarder(r)}>OK</Button>
        : <Button size="small" onClick={() => editer(r)}>Modifier</Button>
    },
  ]

  return editId ? (
    <Form form={form} layout="vertical">
      <Table
        dataSource={etapes}
        rowKey="id"
        size="small"
        pagination={false}
        columns={colonnes}
        expandable={{
          expandedRowKeys: [editId],
          expandedRowRender: (record) => record.id === editId ? (
            <Space wrap>
              {record.etape !== 'Livraison intégration' && (
                <Form.Item name="pourcentage_avancement" label="%" style={{ marginBottom: 0 }}>
                  <InputNumber min={0} max={100} style={{ width: 70 }} />
                </Form.Item>
              )}
              <Form.Item name="date_prevue" label="Date prévue" style={{ marginBottom: 0 }}>
                <DatePicker format="DD/MM/YYYY" />
              </Form.Item>
              <Form.Item name="date_reelle" label="Date réelle" style={{ marginBottom: 0 }}>
                <DatePicker format="DD/MM/YYYY" />
              </Form.Item>
              <Form.Item name="responsable" label="Responsable" style={{ marginBottom: 0 }}>
                <Input style={{ width: 150 }} />
              </Form.Item>
              <Form.Item name="modifie_par" label="Modifié par" style={{ marginBottom: 0 }}>
                <Input style={{ width: 130 }} />
              </Form.Item>
              <Form.Item name="commentaire" label="Commentaire" style={{ marginBottom: 0 }}>
                <Input.TextArea rows={2} style={{ width: 300 }} />
              </Form.Item>
            </Space>
          ) : null,
          showExpandColumn: false,
        }}
      />
    </Form>
  ) : (
    <Table dataSource={etapes} rowKey="id" size="small" pagination={false} columns={colonnes} />
  )
}

export default function EvolutionDetail() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [evolution, setEvolution] = useState(null)
  const [temps, setTemps] = useState(null)
  const [snapshots, setSnapshots] = useState([])
  const [historique, setHistorique] = useState([])

  const charger = () => {
    api.getEvolution(code).then(setEvolution)
    api.getTempsEvolution(code).then(setTemps)
    api.getSnapshots(code).then(setSnapshots)
    api.getHistoriqueEtapes(code).then(setHistorique)
  }

  useEffect(() => { charger() }, [code])

  if (!evolution) return null

  const raf_total = (evolution.raf_dev || 0) + (evolution.raf_testing || 0)
  const tempsTotal = (temps?.dev_total || 0) + (temps?.testing_total || 0)
  const budget = evolution.budget || 0

  const donneesTemps = [
    { name: 'Consommé DEV', valeur: temps?.dev_total || 0 },
    { name: 'Consommé Testing', valeur: temps?.testing_total || 0 },
    { name: 'RAF DEV', valeur: evolution.raf_dev || 0 },
    { name: 'RAF Testing', valeur: evolution.raf_testing || 0 },
  ]

  const donneesAtterrissage = [...snapshots].reverse().map(s => ({
    label: dayjs(s.date_snapshot).format('DD/MM/YY HH:mm'),
    atterrissage: (s.conso_2025 || 0) + (s.temps_dev_consomme || 0) + (s.temps_testing_consomme || 0) + (s.raf_dev || 0) + (s.raf_testing || 0),
  }))

  const colonnesHistorique = [
    { title: 'Date', dataIndex: 'date_modification', key: 'd', width: 140, render: v => dayjs(v).format('DD/MM/YYYY HH:mm') },
    { title: 'Étape', dataIndex: 'etape', key: 'e', width: 180 },
    { title: 'Champ', dataIndex: 'champ_modifie', key: 'c', width: 130 },
    { title: 'Ancienne valeur', dataIndex: 'ancienne_valeur', key: 'av' },
    { title: 'Nouvelle valeur', dataIndex: 'nouvelle_valeur', key: 'nv' },
    { title: 'Par', dataIndex: 'modifie_par', key: 'p', width: 120 },
  ]

  const supprimerSnapshot = async (id) => {
    try {
      await api.deleteSnapshot(id)
      message.success('Snapshot supprimé')
      charger()
    } catch (e) {
      message.error('Erreur lors de la suppression')
    }
  }

  const colonnesSnapshots = [
    { title: 'Date snapshot', dataIndex: 'date_snapshot', key: 'ds', width: 145, render: v => dayjs(v).format('DD/MM/YYYY HH:mm') },
    { title: 'Budget Aha (j)', dataIndex: 'budget', key: 'bu', width: 110, align: 'right', render: formatJours },
    { title: 'Macro chiffrage (j)', dataIndex: 'macro_chiffrage', key: 'mc', width: 140, align: 'right', render: formatJours },
    { title: 'Chiffrage édition (j)', dataIndex: 'chiffrage_edition', key: 'ce', width: 145, align: 'right', render: formatJours },
    { title: 'Conso 2025 (j)', dataIndex: 'conso_2025', key: 'c25', width: 115, align: 'right', render: formatJours },
    { title: 'Tps DEV conso (j)', dataIndex: 'temps_dev_consomme', key: 'tdc', width: 135, align: 'right', render: formatJours },
    { title: 'Tps Testing conso (j)', dataIndex: 'temps_testing_consomme', key: 'ttc', width: 150, align: 'right', render: formatJours },
    { title: 'RAF DEV (j)', dataIndex: 'raf_dev', key: 'rd', width: 100, align: 'right', render: formatJours },
    { title: 'RAF Testing (j)', dataIndex: 'raf_testing', key: 'rt', width: 110, align: 'right', render: formatJours },
    { title: 'RAF Total (j)', dataIndex: 'raf_total', key: 'rtot', width: 100, align: 'right', render: v => <strong>{formatJours(v)}</strong> },
    {
      title: 'Atterrissage (j)', key: 'att', width: 130, align: 'right',
      render: (_, r) => {
        const val = (r.conso_2025 || 0) + (r.temps_dev_consomme || 0) + (r.temps_testing_consomme || 0) + (r.raf_dev || 0) + (r.raf_testing || 0)
        return <strong style={{ color: '#1677ff' }}>{formatJours(val)}</strong>
      }
    },
    {
      title: '', key: 'del', width: 50,
      render: (_, r) => (
        <Popconfirm title="Supprimer ce snapshot ?" onConfirm={() => supprimerSnapshot(r.id)} okText="Oui" cancelText="Non">
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      )
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/evolutions')}>Retour</Button>
        <Title level={3} style={{ margin: 0 }}>{evolution.code} — {evolution.libelle}</Title>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions size="small" column={4} bordered>
          <Descriptions.Item label="Équipe">{evolution.code_equipe}</Descriptions.Item>
          <Descriptions.Item label="Release">{evolution.code_release || '-'}</Descriptions.Item>
          <Descriptions.Item label="Type"><Tag>{evolution.type_evolution}</Tag></Descriptions.Item>
          <Descriptions.Item label="Statut Aha"><Tag>{evolution.statut_aha}</Tag></Descriptions.Item>
          <Descriptions.Item label="Budget Aha (j)"><strong>{evolution.budget ?? '-'}</strong></Descriptions.Item>
        </Descriptions>
      </Card>

      <Tabs items={[
        {
          key: 'chiffrages', label: 'Chiffrages & RAF',
          children: (
            <Card>
              <SectionChiffrages evolution={evolution} onSaved={charger} />
              <Divider />
              <Row gutter={16} style={{ marginTop: 8 }}>
                <Col span={4}><Statistic title="Budget Aha (j)" value={evolution.budget ?? '-'} /></Col>
                <Col span={4}><Statistic title="Macro chiffrage (j)" value={evolution.macro_chiffrage ?? '-'} /></Col>
                <Col span={4}><Statistic title="Chiffrage édition (j)" value={evolution.chiffrage_edition ?? '-'} /></Col>
                <Col span={4}><Statistic title="Consommé 2025 (j)" value={evolution.conso_2025 ?? '-'} precision={evolution.conso_2025 != null ? 2 : undefined} valueStyle={{ color: '#fa8c16' }} /></Col>
                <Col span={4}><Statistic title="Tps DEV consommé (j)" value={temps?.dev_total ?? 0} precision={2} /></Col>
                <Col span={4}><Statistic title="Tps Testing consommé (j)" value={temps?.testing_total ?? 0} precision={2} /></Col>
                <Col span={4}><Statistic title="RAF Total (j)" value={raf_total} precision={2} valueStyle={{ color: raf_total > budget ? '#cf1322' : '#3f8600' }} /></Col>
              </Row>
              <Divider />
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={donneesTemps}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'jours', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Bar dataKey="valeur" fill="#1677ff" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )
        },
        {
          key: 'etapes', label: 'Étapes',
          children: (
            <Card>
              <SectionEtapes etapes={evolution.etapes} onSaved={charger} />
            </Card>
          )
        },
        {
          key: 'atterrissage', label: 'Atterrissage',
          children: (
            <Card>
              {donneesAtterrissage.length > 0 && (
                <>
                  <Title level={5}>Évolution de l'atterrissage (jours)</Title>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={donneesAtterrissage}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="label" />
                      <YAxis />
                      <Tooltip formatter={v => [`${v.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} j`, 'Atterrissage']} />
                      <Line type="monotone" dataKey="atterrissage" stroke="#1677ff" name="Atterrissage" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                  <Divider />
                </>
              )}
              <Table dataSource={snapshots} columns={colonnesSnapshots} rowKey="id" size="small" pagination={{ pageSize: 20 }} scroll={{ x: 900 }} />
            </Card>
          )
        },
        {
          key: 'temps', label: 'Temps détaillé',
          children: (
            <Card>
              <Table
                dataSource={temps?.detail || []}
                rowKey={(r) => `${r.matricule}-${r.annee}-${r.mois}`}
                size="small"
                pagination={{ pageSize: 20 }}
                columns={[
                  { title: 'Ressource', dataIndex: 'nom', key: 'nom' },
                  { title: 'Équipe', dataIndex: 'equipe', key: 'eq', width: 120 },
                  { title: 'Type', dataIndex: 'type', key: 'type', width: 90, render: v => <Tag color={v === 'DEV' ? 'blue' : 'orange'}>{v}</Tag> },
                  { title: 'Année', dataIndex: 'annee', key: 'an', width: 70 },
                  { title: 'Mois', dataIndex: 'mois', key: 'mo', width: 110, render: v => MOIS_FR[(v || 1) - 1] },
                  { title: 'Jours', dataIndex: 'jours', key: 'j', width: 90, align: 'right', render: formatJours },
                ]}
                summary={() => {
                  const total = (temps?.detail || []).reduce((acc, r) => acc + (r.jours || 0), 0)
                  return (
                    <Table.Summary.Row>
                      <Table.Summary.Cell index={0} colSpan={5}><strong>Total</strong></Table.Summary.Cell>
                      <Table.Summary.Cell index={1} align="right"><strong>{formatJours(total)}</strong></Table.Summary.Cell>
                    </Table.Summary.Row>
                  )
                }}
              />
            </Card>
          )
        },
        {
          key: 'historique', label: 'Historique',
          children: (
            <Card>
              <Table dataSource={historique} columns={colonnesHistorique} rowKey="id" size="small" pagination={{ pageSize: 20 }} />
            </Card>
          )
        },
      ]} />
    </div>
  )
}
