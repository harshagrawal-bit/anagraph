import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Research from './pages/Research.jsx'
import Profile from './pages/Profile.jsx'
import EdgeLibrary from './pages/EdgeLibrary.jsx'
import Vault from './pages/Vault.jsx'

const NAV_ITEMS = [
  { path: '/',           label: 'Dashboard',    icon: '◈' },
  { path: '/research',   label: 'Research',     icon: '⚡' },
  { path: '/edges',      label: 'Edge Library', icon: '◆' },
  { path: '/vault',      label: 'Vault',        icon: '⊞' },
  { path: '/profile',    label: 'Profile',      icon: '⊙' },
]

const styles = {
  app: { display: 'flex', minHeight: '100vh', background: '#0a0e17' },
  sidebar: {
    width: '220px', flexShrink: 0, background: '#0d1117',
    borderRight: '1px solid #1e2738', display: 'flex', flexDirection: 'column',
    padding: '24px 0',
  },
  logo: { padding: '0 24px 28px', borderBottom: '1px solid #1e2738', marginBottom: '8px' },
  logoText: { fontSize: '18px', fontWeight: 700, color: '#60a5fa', letterSpacing: '-0.3px' },
  logoSub: { fontSize: '10px', color: '#4a5568', marginTop: '2px', letterSpacing: '1.5px', textTransform: 'uppercase' },
  navLink: {
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '10px 24px', color: '#718096', textDecoration: 'none',
    fontSize: '13px', fontWeight: 500, transition: 'all 0.15s',
    borderLeft: '2px solid transparent',
  },
  navLinkActive: { color: '#60a5fa', background: '#111827', borderLeftColor: '#60a5fa' },
  navIcon: { fontSize: '14px', width: '16px', textAlign: 'center' },
  main: { flex: 1, overflow: 'auto' },
  statusBar: {
    marginTop: 'auto', padding: '16px 24px', borderTop: '1px solid #1e2738',
    fontSize: '11px', color: '#4a5568',
  },
  statusDot: { display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#48bb78', marginRight: '6px' },
}

function Sidebar() {
  return (
    <div style={styles.sidebar}>
      <div style={styles.logo}>
        <div style={styles.logoText}>HedgeOS</div>
        <div style={styles.logoSub}>AI Research Intelligence</div>
      </div>
      <nav>
        {NAV_ITEMS.map(({ path, label, icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            style={({ isActive }) => ({
              ...styles.navLink,
              ...(isActive ? styles.navLinkActive : {}),
            })}
          >
            <span style={styles.navIcon}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={styles.statusBar}>
        <span style={styles.statusDot} />
        API Connected
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.app}>
        <Sidebar />
        <main style={styles.main}>
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/research" element={<Research />} />
            <Route path="/edges"    element={<EdgeLibrary />} />
            <Route path="/vault"    element={<Vault />} />
            <Route path="/profile"  element={<Profile />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
