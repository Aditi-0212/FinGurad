import { useEffect, useState } from 'react'
import api from '../api/client'
import RiskBadge from '../components/RiskBadge'

export default function Budgets() {
  const [budgets, setBudgets] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getBudgets().then(setBudgets).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="p-8 text-risk-high">Could not reach the backend ({error}).</div>

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Budget Monitoring</h1>
      <p className="text-sm text-ink-muted mb-6">Budget vs actual spending by department and month.</p>

      <div className="bg-base-surface border border-base-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-base-border text-left text-[11px] uppercase tracking-wide text-ink-faint">
              <th className="px-5 py-3 font-medium">Department</th>
              <th className="px-5 py-3 font-medium">Month</th>
              <th className="px-5 py-3 font-medium text-right">Budget</th>
              <th className="px-5 py-3 font-medium text-right">Actual</th>
              <th className="px-5 py-3 font-medium text-right">Utilization</th>
              <th className="px-5 py-3 font-medium text-right">Overrun</th>
              <th className="px-5 py-3 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-base-border">
            {budgets.map((b, i) => (
              <tr key={i} className="hover:bg-base-surface2">
                <td className="px-5 py-3 text-ink-primary">{b.department}</td>
                <td className="px-5 py-3 text-ink-muted font-mono">{b.month}</td>
                <td className="px-5 py-3 text-right font-mono text-ink-muted">₹{b.budget.toLocaleString('en-IN')}</td>
                <td className="px-5 py-3 text-right font-mono text-ink-primary">₹{b.actual_spending.toLocaleString('en-IN')}</td>
                <td className="px-5 py-3 text-right font-mono text-ink-muted">{b.utilization_pct}%</td>
                <td className="px-5 py-3 text-right font-mono">
                  {b.overrun_pct > 0 ? <span className="text-risk-high">+{b.overrun_pct}%</span> : <span className="text-ink-faint">—</span>}
                </td>
                <td className="px-5 py-3">
                  <RiskBadge level={b.risk_level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
