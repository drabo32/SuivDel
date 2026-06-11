import React, { useState, useEffect } from 'react'
import { Tabs, Table, Button, Form, Input, Select, Space, Popconfirm, Typography, Modal, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { api } from '../api/client'

const { Title } = Typography

function ReleasesTab() {
  const [releases, setReleases] = useState([])
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [form] = Form.useForm()

  const charger = () => api.getReleases().then(setReleases)
  useEffect(() => { charger() }, [])

  const ouvrir = (item = null) => { setEditItem(item); form.setFieldsValue(item || {}); setModal(true) }

  const sauvegarder = async () => {
    const values = await form.validateFields()
    try {
      if (editItem) await api.updateRelease(editItem.code, values)
      else await api.createRelease(values)
      message.success('Sauvegardé')
      setModal(false)
      charger()
    } catch (e) { message.error(e.message) }
  }

  const colonnes = [
    { title: 'Code', dataIndex: 'code', key: 'code', width: 120 },
    { title: 'Libellé', dataIndex: 'libelle', key: 'libelle' },
    { title: 'Version', dataIndex: 'version', key: 'version', width: 100 },
    { title: 'Mois', dataIndex: 'mois', key: 'mois', width: 70 },
    { title: 'Année', dataIndex: 'annee', key: 'annee', width: 80 },
    { title: '', key: 'actions', width: 60, render: (_, r) => <Button size="small" icon={<EditOutlined />} onClick={() => ouvrir(r)} /> },
  ]

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => ouvrir()} style={{ marginBottom: 12 }}>Nouvelle release</Button>
      <Table dataSource={releases} columns={colonnes} rowKey="code" size="small" pagination={false} />
      <Modal open={modal} title={editItem ? 'Modifier release' : 'Nouvelle release'} onOk={sauvegarder} onCancel={() => setModal(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="Code" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="libelle" label="Libellé" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="version" label="Version (ex: 8.23)" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="mois" label="Mois" rules={[{ required: true }]}><Input type="number" min={1} max={12} /></Form.Item>
          <Form.Item name="annee" label="Année" rules={[{ required: true }]}><Input type="number" /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function WorkspacesTab() {
  const [mappings, setMappings] = useState([])
  const [equipes, setEquipes] = useState([])

  useEffect(() => {
    api.getWorkspaces().then(setMappings)
    api.getEquipes().then(setEquipes)
  }, [])

  const maj = async (workspace, code_equipe) => {
    try {
      await api.updateWorkspace(workspace, code_equipe)
      message.success('Mis à jour')
    } catch (e) { message.error('Erreur lors de la mise à jour') }
  }

  const colonnes = [
    { title: 'Workspace Aha', dataIndex: 'workspace_aha', key: 'ws' },
    {
      title: 'Équipe', dataIndex: 'code_equipe', key: 'eq', render: (val, row) => (
        <Select defaultValue={val} style={{ width: 160 }} onChange={v => maj(row.workspace_aha, v)}
          options={equipes.map(e => ({ value: e.code, label: e.libelle }))} />
      )
    },
  ]

  return <Table dataSource={mappings} columns={colonnes} rowKey="workspace_aha" size="small" pagination={false} />
}

function TimeNiv2Tab() {
  const [mappings, setMappings] = useState([])
  const [equipes, setEquipes] = useState([])
  const [modal, setModal] = useState(false)
  const [form] = Form.useForm()

  const charger = () => api.getTimeNiv2Mappings().then(setMappings)
  useEffect(() => { charger(); api.getEquipes().then(setEquipes) }, [])

  const sauvegarder = async () => {
    const { time_niv2, code_equipe, type_equipe } = await form.validateFields()
    try {
      await api.saveTimeNiv2Mapping(time_niv2, code_equipe, type_equipe)
      message.success('Sauvegardé')
      setModal(false)
      form.resetFields()
      charger()
    } catch (e) { message.error(e.message) }
  }

  const supprimer = async (time_niv2) => {
    try {
      await api.deleteTimeNiv2Mapping(time_niv2)
      message.success('Supprimé')
      charger()
    } catch (e) { message.error('Erreur lors de la suppression') }
  }

  const colonnes = [
    { title: 'Time_Niv2 (ChangePoint)', dataIndex: 'time_niv2', key: 'niv2' },
    { title: 'Équipe', dataIndex: 'code_equipe', key: 'eq', width: 180, render: v => equipes.find(e => e.code === v)?.libelle || v },
    { title: 'Type', dataIndex: 'type_equipe', key: 'type', width: 100 },
    {
      title: '', key: 'actions', width: 60,
      render: (_, r) => (
        <Popconfirm title="Supprimer ?" onConfirm={() => supprimer(r.time_niv2)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      )
    },
  ]

  return (
    <>
      <p style={{ color: '#888', marginBottom: 12 }}>
        Ces correspondances rattachent le temps ChangePoint à une équipe.
        Les valeurs <b>Time_Niv2</b> non mappées apparaissent dans le rapport d'import.
      </p>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModal(true)} style={{ marginBottom: 12 }}>Ajouter</Button>
      <Table dataSource={mappings} columns={colonnes} rowKey="time_niv2" size="small" pagination={false} />
      <Modal open={modal} title="Nouveau mapping Time_Niv2" onOk={sauvegarder} onCancel={() => { setModal(false); form.resetFields() }}>
        <Form form={form} layout="vertical">
          <Form.Item name="time_niv2" label="Valeur Time_Niv2 (ChangePoint)" rules={[{ required: true }]}>
            <Input placeholder="ex: 0346-AI Prévoyance" />
          </Form.Item>
          <Form.Item name="code_equipe" label="Équipe" rules={[{ required: true }]}>
            <Select options={equipes.map(e => ({ value: e.code, label: e.libelle }))} />
          </Form.Item>
          <Form.Item name="type_equipe" label="Type" rules={[{ required: true }]}>
            <Select options={[{ value: 'DEV', label: 'DEV' }, { value: 'TESTING', label: 'TESTING' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default function Admin() {
  return (
    <div>
      <Title level={3}>Administration</Title>
      <Tabs items={[
        { key: 'releases', label: 'Releases / Versions', children: <ReleasesTab /> },
        { key: 'workspaces', label: 'Workspaces Aha → Équipe', children: <WorkspacesTab /> },
        { key: 'timeniv2', label: 'Time_Niv2 → Équipe', children: <TimeNiv2Tab /> },
      ]} />
    </div>
  )
}
