import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import AnomaliesList from './pages/AnomaliesList'
import Investigation from './pages/Investigation'
import Budgets from './pages/Budgets'
import Receivables from './pages/Receivables'
import Cashflow from './pages/Cashflow'
import Assistant from './pages/Assistant'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/anomalies" element={<AnomaliesList />} />
          <Route path="/investigate/:anomalyId" element={<Investigation />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/receivables" element={<Receivables />} />
          <Route path="/cashflow" element={<Cashflow />} />
          <Route path="/assistant" element={<Assistant />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}