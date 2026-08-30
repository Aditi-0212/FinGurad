import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import RiskBadge from '../components/RiskBadge'

const riskLevel = (score) => (score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW')

export default function AnomaliesList() {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .getAnomalies()
      .then((data) => setAnomalies(data.sort((a, b) => b.risk_score - a.risk_score)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-ink-muted">Scanning transactions…</div>
  if (error) return <div className="p-8 text-risk-high">Could not reach the backend ({error}).</div>

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Risk Alerts</h1>
      <p className="text-sm text-ink-muted mb-6">{anomalies.length} anomalies detected across all transactions.</p>

      <div className="bg-base-surface border border-base-border rounded-lg divide-y divide-base-border overflow-hidden">
        {anomalies.map((a) => (
          <Link
            key={a.id}
            to={`/investigate/${a.id}`}
            className="flex items-center justify-between px-5 py-3.5 hover:bg-base-surface2 transition-colors"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-ink-primary">
                  {a.type === 'duplicate_invoice' ? 'Potential Duplicate Invoice' : 'Transaction Anomaly'}
                </p>
                <span className="text-[11px] text-ink-faint font-mono">{a.status}</span>
              </div>
              <p className="text-xs text-ink-muted font-mono mt-0.5">{a.transaction_id}</p>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <span className="font-mono text-sm text-ink-muted">{a.risk_score}/100</span>
              <RiskBadge level={riskLevel(a.risk_score)} />
            </div>
          </Link>
        ))}
        {anomalies.length === 0 && <div className="px-5 py-8 text-center text-ink-faint text-sm">No anomalies detected.</div>}
      </div>
    </div>
  )
}
