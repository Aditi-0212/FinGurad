import { useEffect, useState } from 'react'
import api from '../api/client'
import RiskBadge from '../components/RiskBadge'

export default function Receivables() {
  const [receivables, setReceivables] = useState([])
  const [repeatOffenders, setRepeatOffenders] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.getReceivables(), api.getRepeatedLatePayers()])
      .then(([r, o]) => {
        setReceivables(r.sort((a, b) => (a.priority === b.priority ? b.days_overdue - a.days_overdue : a.priority === 'HIGH' ? -1 : 1)))
        setRepeatOffenders(o)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="p-8 text-risk-high">Could not reach the backend ({error}).</div>

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Receivables</h1>
      <p className="text-sm text-ink-muted mb-6">Outstanding invoices, prioritized by value and days overdue.</p>

      {repeatOffenders.length > 0 && (
        <div className="mb-6 bg-risk-medium/10 border border-risk-medium/30 rounded-lg p-4">
          <p className="text-sm text-risk-medium font-medium mb-1">Repeated Late Payers</p>
          <p className="text-sm text-ink-muted">
            {repeatOffenders.map((o) => `${o.customer} (${o.overdue_invoice_count} overdue)`).join(', ')}
          </p>
        </div>
      )}

      <div className="bg-base-surface border border-base-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-base-border text-left text-[11px] uppercase tracking-wide text-ink-faint">
              <th className="px-5 py-3 font-medium">Invoice</th>
              <th className="px-5 py-3 font-medium">Customer</th>
              <th className="px-5 py-3 font-medium text-right">Amount</th>
              <th className="px-5 py-3 font-medium text-right">Days Overdue</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Priority</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-base-border">
            {receivables.map((r) => (
              <tr key={r.invoice_id} className="hover:bg-base-surface2">
                <td className="px-5 py-3 font-mono text-ink-muted">{r.invoice_id}</td>
                <td className="px-5 py-3 text-ink-primary">{r.customer}</td>
                <td className="px-5 py-3 text-right font-mono text-ink-primary">₹{r.amount.toLocaleString('en-IN')}</td>
                <td className="px-5 py-3 text-right font-mono text-ink-muted">{r.days_overdue > 0 ? r.days_overdue : '—'}</td>
                <td className="px-5 py-3 text-ink-muted">{r.payment_status}</td>
                <td className="px-5 py-3">
                  <RiskBadge level={r.priority} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
