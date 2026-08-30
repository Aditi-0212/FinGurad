import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'
import RiskBadge from '../components/RiskBadge'

const formatCompactINR = (value) => {
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`
  if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`
  return `₹${value}`
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [budgets, setBudgets] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [cashflow, setCashflow] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.getDashboard(), api.getBudgets(), api.getAnomalies('Open'), api.getCashflow()])
      .then(([d, b, a, cf]) => {
        setDashboard(d)
        setBudgets(b)
        setAnomalies(a.sort((x, y) => y.risk_score - x.risk_score).slice(0, 5))
        setCashflow(cf)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-ink-muted">Loading dashboard…</div>
  if (error)
    return (
      <div className="p-8 text-risk-high">
        Could not reach the backend ({error}). Confirm the API is running and CORS/DATABASE_URL are set.
      </div>
    )

  const budgetOverruns = budgets.filter((b) => b.overrun_pct > 0).slice(0, 6)
  const forecastChartData = cashflow?.forecast_points
    ?.filter((_, i) => i % 5 === 0)
    .map((p) => ({ date: p.date.slice(5), cash: Math.round(p.projected_cash) }))

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <h1 className="font-display text-xl font-semibold text-ink-primary">Financial Overview</h1>
          <p className="text-sm text-ink-muted mt-0.5">Real-time risk and health summary across the company.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Financial Health"
          value={`${dashboard.financial_health_score}/100`}
          tone={dashboard.financial_health_score >= 70 ? 'good' : dashboard.financial_health_score >= 40 ? 'warn' : 'bad'}
        />
        <StatCard
          label="Open Risk Alerts"
          value={dashboard.open_anomalies}
          sublabel={`${dashboard.high_risk_anomalies} high-risk`}
          tone={dashboard.high_risk_anomalies > 0 ? 'warn' : 'default'}
        />
        <StatCard
          label="Budget Overruns"
          value={dashboard.budget_high_risk_count}
          sublabel="departments at HIGH risk"
          tone={dashboard.budget_high_risk_count > 0 ? 'warn' : 'default'}
        />
        <StatCard
          label="Cash Runway"
          value={dashboard.cashflow_days_until_deficit != null ? `${dashboard.cashflow_days_until_deficit}d` : '—'}
          sublabel={dashboard.cashflow_days_until_deficit != null ? 'until projected deficit' : 'no deficit projected'}
          tone={dashboard.cashflow_days_until_deficit != null && dashboard.cashflow_days_until_deficit < 30 ? 'bad' : 'default'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-base-surface border border-base-border rounded-lg p-5">
          <h2 className="text-sm font-medium text-ink-primary mb-1">High Priority Alerts</h2>
          <p className="text-xs text-ink-muted mb-4">Highest risk-score open anomalies awaiting review.</p>
          <div className="space-y-2">
            {anomalies.length === 0 && <p className="text-sm text-ink-faint py-4">No open anomalies right now.</p>}
            {anomalies.map((a) => (
              <Link
                key={a.id}
                to={`/investigate/${a.id}`}
                className="flex items-center justify-between px-3 py-2.5 rounded-md bg-base-surface2 hover:bg-base-border/60 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm text-ink-primary font-medium truncate">
                    {a.type === 'duplicate_invoice' ? 'Potential Duplicate Invoice' : 'Transaction Anomaly'}
                  </p>
                  <p className="text-xs text-ink-muted font-mono">{a.transaction_id}</p>
                </div>
                <RiskBadge level={a.risk_score >= 70 ? 'HIGH' : a.risk_score >= 40 ? 'MEDIUM' : 'LOW'} />
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-base-surface border border-base-border rounded-lg p-5">
          <h2 className="text-sm font-medium text-ink-primary mb-1">Budget vs Actual</h2>
          <p className="text-xs text-ink-muted mb-4">Departments currently over their allocated budget.</p>
          {budgetOverruns.length === 0 ? (
            <p className="text-sm text-ink-faint py-4">No budget overruns.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={budgetOverruns} margin={{ left: 8, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#232C36" vertical={false} />
                <XAxis dataKey="department" tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={{ stroke: '#232C36' }} tickLine={false} />
                <YAxis tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={formatCompactINR} width={56} />
                <Tooltip
                  contentStyle={{ background: '#131920', border: '1px solid #232C36', borderRadius: 6, fontSize: 12 }}
                  formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
                />
                <Bar dataKey="budget" fill="#2DD4BF" fillOpacity={0.35} radius={[3, 3, 0, 0]} name="Budget" />
                <Bar dataKey="actual_spending" fill="#F59E0B" radius={[3, 3, 0, 0]} name="Actual" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="bg-base-surface border border-base-border rounded-lg p-5">
        <h2 className="text-sm font-medium text-ink-primary mb-1">Cash Position Forecast</h2>
        <p className="text-xs text-ink-muted mb-4">
          Projected cash over the next 60 days based on current spending and collection trends. This is an estimate, not a
          guarantee.
        </p>
        {forecastChartData && (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={forecastChartData} margin={{ left: 8, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#232C36" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={{ stroke: '#232C36' }} tickLine={false} />
              <YAxis tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={formatCompactINR} width={56} />
              <Tooltip
                contentStyle={{ background: '#131920', border: '1px solid #232C36', borderRadius: 6, fontSize: 12 }}
                formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
              />
              <Line type="monotone" dataKey="cash" stroke="#2DD4BF" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}