import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined, UploadOutlined, SettingOutlined, TeamOutlined,
  RocketOutlined, BarChartOutlined, WarningOutlined, HistoryOutlined,
} from '@ant-design/icons'

import Dashboard from './pages/Dashboard'
import EvolutionDetail from './pages/EvolutionDetail'
import Import from './pages/Import'
import Admin from './pages/Admin'
import DashboardTesting from './pages/DashboardTesting'
import HorsEvolutions from './pages/HorsEvolutions'
import ControleAha from './pages/ControleAha'
import HistoriqueRelease from './pages/HistoriqueRelease'

const { Sider, Content } = Layout

const MENU_ITEMS = [
  { key: '/', icon: <DashboardOutlined />, label: <Link to="/">Dashboard</Link> },
  { key: '/dashboard/testing', icon: <RocketOutlined />, label: <Link to="/dashboard/testing">Pôle Testing</Link> },
  { key: '/historique-release', icon: <HistoryOutlined />, label: <Link to="/historique-release">Historique releases</Link> },
  { key: '/hors-evolutions', icon: <BarChartOutlined />, label: <Link to="/hors-evolutions">Hors évolutions</Link> },
  { key: '/controle-aha', icon: <WarningOutlined />, label: <Link to="/controle-aha">Contrôle Aha</Link> },
  { key: '/import', icon: <UploadOutlined />, label: <Link to="/import">Import</Link> },
  { key: '/admin', icon: <SettingOutlined />, label: <Link to="/admin">Administration</Link> },
]

export default function App() {
  const location = useLocation()
  const selectedKey = location.pathname === '/' ? '/' : '/' + location.pathname.split('/')[1]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark" style={{ position: 'fixed', height: '100vh', left: 0, top: 0, zIndex: 100 }}>
        <div style={{ color: '#fff', fontWeight: 'bold', fontSize: 15, padding: '18px 16px 10px', borderBottom: '1px solid #333' }}>
          Suivi Évolutions
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={MENU_ITEMS}
          style={{ marginTop: 8 }}
        />
      </Sider>
      <Layout style={{ marginLeft: 220 }}>
        <Content style={{ padding: 24, background: '#f5f5f5', minHeight: '100vh' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/evolutions/:code" element={<EvolutionDetail />} />
            <Route path="/dashboard/testing" element={<DashboardTesting />} />
            <Route path="/historique-release" element={<HistoriqueRelease />} />
            <Route path="/hors-evolutions" element={<HorsEvolutions />} />
            <Route path="/controle-aha" element={<ControleAha />} />
            <Route path="/import" element={<Import />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}
