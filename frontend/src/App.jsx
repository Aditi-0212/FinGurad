import { lazy, Suspense } from 'react'
import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Auth from './pages/Auth'
import api from './api/client'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const AnomaliesList = lazy(() => import('./pages/AnomaliesList'))
const Investigation = lazy(() => import('./pages/Investigation'))
const Budgets = lazy(() => import('./pages/Budgets'))
const Receivables = lazy(() => import('./pages/Receivables'))
const Cashflow = lazy(() => import('./pages/Cashflow'))
const Assistant = lazy(() => import('./pages/Assistant'))
const Ingestion = lazy(() => import('./pages/Ingestion'))
const Analysis = lazy(() => import('./pages/Analysis'))

function WorkspaceApp({ identity, onLogout }) {
  return (
    <BrowserRouter>
      <Suspense fallback={<div className="p-8 text-sm text-ink-muted">Loading…</div>}>
        <Routes>
          <Route element={<Layout identity={identity} onLogout={onLogout} />}>
            <Route path="/" element={<Ingestion />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/anomalies" element={<AnomaliesList />} />
            <Route path="/investigate/:anomalyId" element={<Investigation />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/receivables" element={<Receivables />} />
            <Route path="/cashflow" element={<Cashflow />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/ingestion" element={<Ingestion />} />
            <Route path="/analysis/:runId" element={<Analysis />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default function App() {
  const [identity, setIdentity] = useState(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('finguard_token')
    if (!token) {
      setChecking(false)
      return
    }
    api.getCurrentUser()
      .then((user) => setIdentity(user))
      .catch(() => {
        localStorage.removeItem('finguard_token')
        localStorage.removeItem('finguard_identity')
      })
      .finally(() => setChecking(false))
  }, [])

  const logout = () => {
    localStorage.removeItem('finguard_token')
    localStorage.removeItem('finguard_identity')
    window.location.replace('/')
  }

  if (checking) return <div className="min-h-screen bg-base-bg p-8 text-sm text-ink-muted">Checking workspace…</div>
  if (!identity) return <Auth onAuthenticated={setIdentity} />
  return <WorkspaceApp identity={identity} onLogout={logout} />
}
