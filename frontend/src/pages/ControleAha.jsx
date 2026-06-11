import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Typography, Alert, Badge, Space } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { formatMoisKey } from '../utils'

const { Title, Text } = Typography

export default function ControleAha() {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.getControleAha().then(setData).catch(console.error)
  }, [])

  const colonnes = [
    {
      title: 'Code évolution',
      dataIndex: 'code',
      key: 'code',
      width: 160,
      render: v => (
        <a onClick={() => navigate(`/evolutions/${v}`)} style={{ fontFamily: 'monospace' }}>
          {v}
        </a>
      ),
    },
    {
      title: 'Équipe',
      dataIndex: 'equipe',
      key: 'equipe',
      width: 120,
      render: v => <Tag>{v}</Tag>,
    },
    {
      title: 'Tps DEV (j)',
      dataIndex: 'temps_dev',
      key: 'temps_dev',
      width: 110,
      align: 'right',
      render: v => v > 0 ? <strong>{v.toFixed(2)}</strong> : <span style={{ color: '#d9d9d9' }}>—</span>,
    },
    {
      title: 'Tps Testing (j)',
      dataIndex: 'temps_testing',
      key: 'temps_testing',
      width: 120,
      align: 'right',
      render: v => v > 0 ? v.toFixed(2) : <span style={{ color: '#d9d9d9' }}>—</span>,
    },
    {
      title: 'Mois de données',
      key: 'periode',
      width: 180,
      render: (_, r) => r.nb_mois > 0
        ? <span>{formatMoisKey(r.premier_mois)} → {formatMoisKey(r.dernier_mois)} <Text type="secondary">({r.nb_mois} mois)</Text></span>
        : <span style={{ color: '#d9d9d9' }}>—</span>,
    },
    {
      title: 'Statut',
      key: 'statut',
      width: 200,
      render: () => (
        <Tag color="orange" icon={<WarningOutlined />}>
          Import Aha requis
        </Tag>
      ),
    },
  ]

  const total = data?.total ?? 0

  return (
    <div>
      <Title level={3}>Contrôle import Aha</Title>

      {data && total === 0 && (
        <Alert
          type="success"
          showIcon
          message="Aucune évolution orpheline"
          description="Toutes les évolutions détectées dans ChangePoint ont été importées depuis Aha."
          style={{ marginBottom: 16 }}
        />
      )}

      {data && total > 0 && (
        <Alert
          type="warning"
          showIcon
          icon={<WarningOutlined />}
          message={
            <Space>
              <strong>{total} évolution{total > 1 ? 's' : ''} sans import Aha</strong>
              <Text type="secondary">
                — Ces évolutions ont été créées automatiquement lors d'un import ChangePoint.
                Leur libellé est temporaire (= le code). Importez le fichier Aha pour les enrichir.
              </Text>
            </Space>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Card>
        <Table
          dataSource={data?.evolutions || []}
          columns={colonnes}
          rowKey="code"
          size="small"
          loading={!data}
          pagination={{ pageSize: 50 }}
          rowClassName={() => 'row-warning'}
          locale={{ emptyText: 'Aucune évolution à contrôler' }}
        />
      </Card>

      <style>{`
        .row-warning td { background-color: #fffbe6 !important; }
        .row-warning:hover td { background-color: #fff1b8 !important; }
      `}</style>
    </div>
  )
}
