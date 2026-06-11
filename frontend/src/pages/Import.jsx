import React, { useState, useEffect } from 'react'
import { Card, Upload, Button, Table, Tag, Alert, Space, Typography, Divider } from 'antd'
import { UploadOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import dayjs from 'dayjs'

const { Title, Text } = Typography

function ImportCard({ titre, onImport, loading }) {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async ({ file }) => {
    setResult(null); setError(null)
    try {
      const res = await onImport(file)
      setResult(res)
    } catch (e) {
      setError(e.message)
    }
    return false
  }

  return (
    <Card title={titre} style={{ marginBottom: 24 }}>
      <Upload beforeUpload={() => false} onChange={handleUpload} showUploadList={false} accept=".csv">
        <Button icon={<UploadOutlined />} loading={loading}>Choisir un fichier CSV</Button>
      </Upload>

      {result && (
        <Alert
          style={{ marginTop: 16 }}
          type={result.nb_erreurs > 0 ? 'warning' : 'success'}
          icon={result.nb_erreurs > 0 ? <WarningOutlined /> : <CheckCircleOutlined />}
          message={
            <Space>
              <Text>Créés : <strong>{result.nb_crees}</strong></Text>
              <Text>Mis à jour : <strong>{result.nb_mis_a_jour}</strong></Text>
              <Text>Ignorés : <strong>{result.nb_ignores}</strong></Text>
              <Text>Erreurs : <strong>{result.nb_erreurs}</strong></Text>
            </Space>
          }
          description={result.detail && <pre style={{ fontSize: 12, maxHeight: 150, overflow: 'auto' }}>{result.detail}</pre>}
          showIcon
        />
      )}
      {error && <Alert type="error" message={error} style={{ marginTop: 16 }} />}
    </Card>
  )
}

const colonnesHistorique = [
  { title: 'Date', dataIndex: 'date_import', key: 'date', render: v => dayjs(v).format('DD/MM/YYYY HH:mm'), width: 140 },
  { title: 'Type', dataIndex: 'type_import', key: 'type', render: v => {
    const couleur = { AHA: 'blue', CHANGEPOINT: 'green', INIT: 'purple' }
    return <Tag color={couleur[v] || 'default'}>{v}</Tag>
  }, width: 110 },
  { title: 'Fichier', dataIndex: 'nom_fichier', key: 'fichier' },
  { title: 'Créés', dataIndex: 'nb_crees', key: 'crees', width: 80 },
  { title: 'MàJ', dataIndex: 'nb_mis_a_jour', key: 'maj', width: 80 },
  { title: 'Ignorés', dataIndex: 'nb_ignores', key: 'ignores', width: 80 },
  { title: 'Erreurs', dataIndex: 'nb_erreurs', key: 'erreurs', width: 80, render: v => v > 0 ? <Tag color="red">{v}</Tag> : v },
]

export default function Import() {
  const [historique, setHistorique] = useState([])

  const chargerHistorique = () => api.getHistoriqueImports().then(setHistorique).catch(() => {})

  useEffect(() => { chargerHistorique() }, [])

  return (
    <div>
      <Title level={3}>Import des données</Title>
      <ImportCard
        titre="Import Aha"
        onImport={(file) => api.importAha(file).then(r => { chargerHistorique(); return r })}
      />
      <ImportCard
        titre="Import ChangePoint"
        onImport={(file) => api.importChangepoint(file).then(r => { chargerHistorique(); return r })}
      />
      <ImportCard
        titre="Initialisation depuis SuiviDelivery (Macro chiffrage, Chiffrage édition, RAF, Date fin)"
        onImport={(file) => api.importInit(file).then(r => { chargerHistorique(); return r })}
      />
      <Divider />
      <Title level={4}>Historique des imports</Title>
      <Table
        dataSource={historique}
        columns={colonnesHistorique}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 20 }}
      />
    </div>
  )
}
