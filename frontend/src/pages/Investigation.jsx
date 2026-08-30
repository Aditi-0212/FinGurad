import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import RiskDial from '../components/RiskDial'

export default function Investigation() {
  const { anomalyId } = useParams()
  const [anomaly, setAnomaly] = useState(null)
  const [transaction, setTransaction] = useState(null)
  const [investigation, setInvestigation] = useState(null)
  const [investigating, setInvestigating] = useState(false)
  const [investigateError, setInvestigateError] = useState(null)

  const [approver, setApprover] = useState('Finance Manager')
  const [comment, setComment] = useState('')
  const [actionResult, setActionResult] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [actionPending, setActionPending] = useState(false)

  const [loadError, setLoadError] = useState(null)

  useEffect(() => {
    api
      .getAnomaly(anomalyId)
      .then((a) => {
        setAnomaly(a)
        return api.getTransaction(a.transaction_id)
      })
      .then(setTransaction)
      .catch((e) => setLoadError(e.message))
  }, [anomalyId])

  const runInvestigation = () => {
    setInvestigating(true)
    setInvestigateError(null)
    api
      .investigateAnomaly(anomalyId)
      .then(setInvestigation)
      .catch((e) =>
        setInvestigateError(
          e.response?.data?.detail || e.message || 'Investigation failed — check the backend has a valid GROQ_API_KEY set.'
        )
      )
      .finally(() => setInvestigating(false))
  }

  const runAction = (actionFn) => {
    if (!investigation) return
    setActionPending(true)
    setActionError(null)
    actionFn({ investigation_id: investigation.id, user: approver, comment: comment || null })
      .then(setActionResult)
      .catch((e) => setActionError(e.response?.data?.detail || e.message))
      .finally(() => setActionPending(false))
  }

  if (loadError) return <div className="p-8 text-risk-high">Could not load anomaly {anomalyId}: {loadError}</div>
  if (!anomaly || !transaction) return <div className="p-8 text-ink-muted">Loading…</div>

  const riskScore = investigation?.risk_score ?? anomaly.risk_score

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <Link to="/anomalies" className="text-xs text-ink-muted hover:text-accent">
        ← Back to Risk Alerts
      </Link>

      <div className="mt-3 mb-6">
        <p className="text-xs font-mono text-ink-faint uppercase tracking-wide">Transaction</p>
        <h1 className="font-display text-2xl font-semibold text-ink-primary font-tabular">
          ₹{transaction.amount.toLocaleString('en-IN')}
        </h1>
        <p className="text-sm text-ink-muted mt-0.5">
          {transaction.vendor_name} · {transaction.department} · {new Date(transaction.date).toLocaleDateString()} ·{' '}
          <span className="font-mono">{transaction.transaction_id}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-6">
        <div className="bg-base-surface border border-base-border rounded-lg p-5 flex flex-col items-center">
          <p className="text-xs text-ink-muted mb-3">Risk Score</p>
          <RiskDial score={riskScore} />
          <p className="text-[11px] text-ink-faint mt-4 text-center">
            {anomaly.type === 'duplicate_invoice' ? 'Flagged: Potential Duplicate' : 'Flagged: Transaction Anomaly'}
          </p>
        </div>

        <div className="space-y-6">
          {!investigation ? (
            <div className="bg-base-surface border border-base-border rounded-lg p-5">
              <h2 className="text-sm font-medium text-ink-primary mb-1">Why was this flagged?</h2>
              <ul className="mt-3 space-y-1.5">
                {anomaly.signals.map((s, i) => (
                  <li key={i} className="text-sm text-ink-muted flex gap-2">
                    <span className="text-accent">✓</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={runInvestigation}
                disabled={investigating}
                className="mt-5 px-4 py-2 bg-accent text-base-bg text-sm font-medium rounded-md hover:bg-accent-dim transition-colors disabled:opacity-50"
              >
                {investigating ? 'Investigating…' : 'Run AI Investigation'}
              </button>
              {investigateError && (
                <p className="mt-3 text-sm text-risk-high">
                  {investigateError}
                </p>
              )}
            </div>
          ) : (
            <>
              <div className="bg-base-surface border border-base-border rounded-lg p-5">
                <h2 className="text-sm font-medium text-ink-primary mb-3">Supporting Evidence</h2>
                <ul className="space-y-1.5">
                  {investigation.evidence.map((e, i) => (
                    <li key={i} className="text-sm text-ink-muted flex gap-2">
                      <span className="text-accent">✓</span>
                      <span>{e}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-base-surface border border-base-border rounded-lg p-5">
                <h2 className="text-sm font-medium text-ink-primary mb-2">AI Investigation</h2>
                <p className="text-sm text-ink-muted leading-relaxed">{investigation.ai_explanation}</p>
              </div>

              <div className="bg-accent-soft border border-accent/30 rounded-lg p-5">
                <h2 className="text-sm font-medium text-accent mb-2">Recommendation</h2>
                <p className="text-sm text-ink-primary">{investigation.recommendation}</p>
              </div>

              {!actionResult ? (
                <div className="bg-base-surface border border-base-border rounded-lg p-5">
                  <h2 className="text-sm font-medium text-ink-primary mb-3">Your Decision</h2>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="text-[11px] text-ink-faint uppercase tracking-wide">Reviewer</label>
                      <input
                        value={approver}
                        onChange={(e) => setApprover(e.target.value)}
                        className="mt-1 w-full bg-base-surface2 border border-base-border rounded-md px-3 py-1.5 text-sm text-ink-primary focus:outline-none focus:ring-1 focus:ring-accent"
                      />
                    </div>
                  </div>
                  <label className="text-[11px] text-ink-faint uppercase tracking-wide">Comment (optional)</label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={2}
                    className="mt-1 w-full bg-base-surface2 border border-base-border rounded-md px-3 py-1.5 text-sm text-ink-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  />
                  <div className="flex gap-3 mt-4">
                    <button
                      onClick={() => runAction(api.approveAction)}
                      disabled={actionPending}
                      className="px-4 py-2 bg-risk-low/15 text-risk-low border border-risk-low/30 text-sm font-medium rounded-md hover:bg-risk-low/25 transition-colors disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => runAction(api.escalateAction)}
                      disabled={actionPending}
                      className="px-4 py-2 bg-risk-medium/15 text-risk-medium border border-risk-medium/30 text-sm font-medium rounded-md hover:bg-risk-medium/25 transition-colors disabled:opacity-50"
                    >
                      Escalate
                    </button>
                    <button
                      onClick={() => runAction(api.rejectAction)}
                      disabled={actionPending}
                      className="px-4 py-2 bg-risk-high/15 text-risk-high border border-risk-high/30 text-sm font-medium rounded-md hover:bg-risk-high/25 transition-colors disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                  {actionError && <p className="mt-3 text-sm text-risk-high">{actionError}</p>}
                </div>
              ) : (
                <div className="bg-base-surface border border-base-border rounded-lg p-5">
                  <p className="text-sm text-ink-primary">
                    <span className="font-medium">{actionResult.action}</span> recorded by{' '}
                    <span className="font-medium">{actionResult.user}</span> at{' '}
                    {new Date(actionResult.timestamp).toLocaleString()}.
                  </p>
                  {actionResult.comment && <p className="text-sm text-ink-muted mt-1">"{actionResult.comment}"</p>}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
