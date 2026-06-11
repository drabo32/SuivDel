import React, { useState, useEffect, useMemo } from 'react'
import { Card, Select, Typography, Space, Tag, Collapse, Empty, Spin, Row, Col, Statistic, Divider, List } from 'antd'
import { PlusOutlined, MinusOutlined, SwapOutlined, HistoryOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const { Title, Text } = Typography

const formatDateTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

function ListeEvolutions({ items, couleur, icone, titre }) {
  const navigate = useNavigate()
  if (!items.length) return null
  return (
    <div style={{ marginBottom: 12 }}>
      <Text strong style={{ color: couleur, display: 'block', marginBottom: 6 }}>
        {icone} {titre} ({items.length})
      </Text>
      <List
        size="small"
        dataSource={items}
        renderItem={item => (
          <List.Item style={{ padding: '3px 0', borderBottom: 'none' }}>
            <Space>
              <a
                onClick={() => navigate(`/evolutions/${item.evolution_code}`)}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              >
                {item.evolution_code}
              </a>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {item.libelle_evolution || '—'}
              </Text>
            </Space>
          </List.Item>
        )}
      />
    </div>
  )
}

function ListeChangementsStatut({ items }) {
  if (!items.length) return null
  const navigate = useNavigate()
  return (
    <div>
      <Text strong style={{ color: '#d46b08', display: 'block', marginBottom: 6 }}>
        <SwapOutlined /> Changements de statut ({items.length})
      </Text>
      <List
        size="small"
        dataSource={items}
        renderItem={item => (
          <List.Item style={{ padding: '3px 0', borderBottom: 'none' }}>
            <Space wrap>
              <a
                onClick={() => navigate(`/evolutions/${item.evolution_code}`)}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              >
                {item.evolution_code}
              </a>
              <Text type="secondary" style={{ fontSize: 12 }}>{item.libelle_evolution || '—'}</Text>
              <Tag style={{ fontSize: 11 }}>{item.ancienne_valeur}</Tag>
              <Text>→</Text>
              <Tag color="blue" style={{ fontSize: 11 }}>{item.nouvelle_valeur}</Tag>
            </Space>
          </List.Item>
        )}
      />
    </div>
  )
}

export default function HistoriqueRelease() {
  const [releases, setReleases] = useState([])
  const [releaseCode, setReleaseCode] = useState(null)
  const [releaseLabel, setReleaseLabel] = useState('')
  const [historique, setHistorique] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { api.getReleases().then(setReleases) }, [])

  const charger = (code, label) => {
    if (!code) return
    setLoading(true)
    setHistorique(null)
    setReleaseLabel(label)
    api.getHistoriqueRelease(code)
      .then(r => { setHistorique(r); setLoading(false) })
      .catch(() => { setHistorique({ diffs: [], dates_import: [] }); setLoading(false) })
  }

  // Grouper les diffs par date d'import
  const importGroups = useMemo(() => {
    if (!historique?.diffs?.length) return []
    const groups = {}
    for (const d of historique.diffs) {
      if (!groups[d.date_import]) {
        groups[d.date_import] = { date: d.date_import, id_import: d.id_import, ajouts: [], suppressions: [], changements: [] }
      }
      if (d.type_diff === 'AJOUT') groups[d.date_import].ajouts.push(d)
      else if (d.type_diff === 'SUPPRESSION') groups[d.date_import].suppressions.push(d)
      else groups[d.date_import].changements.push(d)
    }
    return Object.values(groups).sort((a, b) => b.date.localeCompare(a.date))
  }, [historique])

  const collapseItems = importGroups.map((group, idx) => {
    const nbAjouts = group.ajouts.length
    const nbSupp = group.suppressions.length
    const nbChgt = group.changements.length
    const total = nbAjouts + nbSupp + nbChgt

    return {
      key: group.date,
      label: (
        <Space wrap>
          <HistoryOutlined style={{ color: '#8c8c8c' }} />
          <Text strong>{formatDateTime(group.date)}</Text>
          <Divider type="vertical" />
          {nbAjouts > 0 && (
            <Tag color="success" icon={<PlusOutlined />}>{nbAjouts} ajout{nbAjouts > 1 ? 's' : ''}</Tag>
          )}
          {nbSupp > 0 && (
            <Tag color="error" icon={<MinusOutlined />}>{nbSupp} suppression{nbSupp > 1 ? 's' : ''}</Tag>
          )}
          {nbChgt > 0 && (
            <Tag color="warning" icon={<SwapOutlined />}>{nbChgt} statut{nbChgt > 1 ? 's' : ''}</Tag>
          )}
          {total === 0 && <Tag>Aucun changement</Tag>}
          {idx === 0 && <Tag color="blue">Dernier import</Tag>}
        </Space>
      ),
      children: (
        <div style={{ padding: '4px 8px' }}>
          <ListeEvolutions
            items={group.ajouts}
            couleur="#52c41a"
            icone={<PlusOutlined />}
            titre="Évolutions entrées dans la release"
          />
          {group.ajouts.length > 0 && (group.suppressions.length > 0 || group.changements.length > 0) && (
            <Divider style={{ margin: '8px 0' }} />
          )}
          <ListeEvolutions
            items={group.suppressions}
            couleur="#f5222d"
            icone={<MinusOutlined />}
            titre="Évolutions sorties de la release"
          />
          {group.suppressions.length > 0 && group.changements.length > 0 && (
            <Divider style={{ margin: '8px 0' }} />
          )}
          <ListeChangementsStatut items={group.changements} />
        </div>
      ),
    }
  })

  // Stats globales sur l'historique
  const statsGlobales = useMemo(() => {
    if (!historique?.diffs?.length) return null
    return {
      nbImports: importGroups.length,
      nbAjoutsTotal: historique.diffs.filter(d => d.type_diff === 'AJOUT').length,
      nbSuppTotal: historique.diffs.filter(d => d.type_diff === 'SUPPRESSION').length,
    }
  }, [historique, importGroups])

  return (
    <div>
      <Title level={3}>Historique du contenu des releases</Title>

      <Card style={{ marginBottom: 20 }}>
        <Space>
          <Text strong>Release :</Text>
          <Select
            placeholder="Choisir une release"
            style={{ width: 300 }}
            options={releases.map(r => ({ value: r.code, label: `${r.version} — ${r.libelle}` }))}
            onChange={(v, opt) => { setReleaseCode(v); charger(v, opt?.label || v) }}
          />
        </Space>
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Spin size="large" tip="Chargement de l'historique..." />
        </div>
      )}

      {!loading && historique && importGroups.length === 0 && (
        <Empty
          description={
            <span>
              Aucun historique pour cette release.<br />
              <Text type="secondary">Les imports Aha futurs alimenteront automatiquement cet historique.</Text>
            </span>
          }
          style={{ marginTop: 60 }}
        />
      )}

      {!loading && statsGlobales && (
        <>
          <Row gutter={16} style={{ marginBottom: 20 }}>
            <Col span={8}>
              <Card>
                <Statistic title="Imports tracés" value={statsGlobales.nbImports} suffix="imports" />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Total ajouts"
                  value={statsGlobales.nbAjoutsTotal}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<PlusOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="Total suppressions"
                  value={statsGlobales.nbSuppTotal}
                  valueStyle={{ color: '#f5222d' }}
                  prefix={<MinusOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Collapse
            items={collapseItems}
            defaultActiveKey={importGroups.length > 0 ? [importGroups[0].date] : []}
            style={{ background: '#fff' }}
          />
        </>
      )}
    </div>
  )
}
