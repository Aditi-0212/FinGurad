import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import api from '../api/client'
import StatCard from '../components/StatCard'

const formatCompactINR = (value) => {
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`
  if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`
  return `₹${value}`
}

export default function Cashflow() {
  const [forecast, setForecast] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getCashflow().then(setForecast).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="p-8 text-risk-high">Could not reach the backend ({error}).</div>
  if (!forecast) return <div className="p-8 text-ink-muted">Loading…</div>

  const chartData = forecast.forecast_points.map((p) => ({ date: p.date.slice(5), cash: Math.round(p.projected_cash) }))

  if (chartData.length === 0) return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Cash Flow Forecast</h1>
      <div className="mt-6 rounded-lg border border-base-border bg-base-surface p-8 text-center">
        <p className="text-sm text-ink-primary">Cash flow can’t be projected from this workspace yet.</p>
        <p className="mt-1 text-xs text-ink-faint">Upload transaction history and receivables to create this forecast.</p>
      </div>
    </div>
  )

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Cash Flow Forecast</h1>
      <p className="text-sm text-ink-muted mb-6">
        Estimate based on recent spending and collection trends — not a guarantee. Refresh assumptions regularly.
      </p>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard label="Current Cash" value={`₹${forecast.current_cash_estimate.toLocaleString('en-IN')}`} />
        <StatCard
          label="Daily Trend"
          value={`₹${Math.round(forecast.daily_net_change_trend).toLocaleString('en-IN')}/day`}
          tone={forecast.daily_net_change_trend < 0 ? 'bad' : 'good'}
        />
        <StatCard
          label="Deficit Projection"
          value={forecast.days_until_deficit != null ? `${forecast.days_until_deficit} days` : 'None projected'}
          sublabel={forecast.projected_deficit_date || undefined}
          tone={forecast.days_until_deficit != null && forecast.days_until_deficit < 30 ? 'bad' : 'default'}
        />
      </div>

      <div className="bg-base-surface border border-base-border rounded-lg p-5">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ left: 8, right: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#232C36" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={{ stroke: '#232C36' }} tickLine={false} />
            <YAxis tick={{ fill: '#8B96A3', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={formatCompactINR} width={56} />
            <Tooltip
              contentStyle={{ background: '#131920', border: '1px solid #232C36', borderRadius: 6, fontSize: 12 }}
              formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
            />
            <ReferenceLine y={0} stroke="#F87171" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="cash" stroke="#2DD4BF" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
