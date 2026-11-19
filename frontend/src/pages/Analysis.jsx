import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api/client'

const currency = (amount) => `₹${Number(amount || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function Analysis() {
  const { runId } = useParams()
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    let timer
    const load = async () => {
      try {
        const next = await api.getIngestionRun(runId)
        if (cancelled) return
        setResult(next)
        if (next.run.status === 'processing' || next.run.status === 'validating') {
          timer = window.setTimeout(load, 1200)
        }
      } catch (e) {
        if (!cancelled) setError(e.response?.data?.detail || e.message || 'Could not load this analysis')
      }
    }
    load()
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [runId])

  if (error) return <div className="p-8 text-risk-high">{error}</div>
  if (!result) return <div className="p-8 text-ink-muted">Opening analysis…</div>
  const { run, report } = result
  const processing = run.status === 'processing' || run.status === 'validating'

  if (processing) return (
    <div className="min-h-screen px-6 py-16 md:px-10">
      <div className="mx-auto max-w-2xl rounded-xl border border-base-border bg-base-surface p-8">
        <p className="text-xs uppercase tracking-[0.2em] text-accent">Analysis in progress</p>
        <h1 className="mt-3 font-display text-2xl font-semibold text-ink-primary">Preparing your finance report</h1>
        <p className="mt-2 text-sm text-ink-muted">{run.filename} · {Number(run.rows_received).toLocaleString()} rows imported</p>
        <div className="mt-7 h-1.5 overflow-hidden rounded-full bg-base-bg"><div className="h-full w-1/2 animate-pulse rounded-full bg-accent" /></div>
        <p className="mt-4 text-xs text-ink-faint">The risk scan runs once for this upload. This page will show your report as soon as it finishes.</p>
      </div>
    </div>
  )

  if (run.status === 'failed') return (
    <div className="p-8">
      <div className="mx-auto max-w-3xl rounded-xl border border-risk-high/30 bg-base-surface p-6">
        <h1 className="text-xl font-semibold text-ink-primary">Analysis could not finish</h1>
        <p className="mt-2 text-sm text-risk-high">{run.error || 'The uploaded file could not be processed.'}</p>
        <Link to="/ingestion" className="mt-5 inline-block text-sm text-accent">Try another file →</Link>
      </div>
    </div>
  )

  if (!['transactions', 'bundle'].includes(run.dataset_type)) {
    const labels = { vendors: 'Vendor data imported', budgets: 'Budget data imported', receivables: 'Receivables imported' }
    const nextStep = run.dataset_type === 'vendors'
      ? 'Your vendor profiles are ready. Upload transactions next to run duplicate detection and transaction risk analysis. The vendor_id values in the transaction file should match the vendor file.'
      : 'Your records are saved in this company workspace. Upload a transactions file to run or refresh transaction risk analysis.'
    return (
      <div className="min-h-screen px-6 py-10 md:px-10">
        <div className="mx-auto max-w-4xl">
          <p className="text-xs uppercase tracking-[0.2em] text-accent">Import complete</p>
          <h1 className="mt-2 font-display text-2xl font-semibold text-ink-primary">{labels[run.dataset_type] || 'File imported'}</h1>
          <p className="mt-1 text-sm text-ink-muted">{run.filename} · {Number(run.rows_received).toLocaleString()} rows received</p>

          <div className="mt-7 grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              ['Rows imported', run.rows_received],
              ['New records', run.rows_created],
              ['Updated records', run.rows_updated],
              ['Vendor profiles', report?.vendors ?? 0],
            ].map(([label, value]) => <div key={label} className="rounded-lg border border-base-border bg-base-surface p-5">
              <p className="text-xs text-ink-muted">{label}</p><p className="mt-2 font-display text-2xl font-semibold text-ink-primary">{Number(value || 0).toLocaleString()}</p>
            </div>)}
          </div>

          <section className="mt-6 rounded-xl border border-accent/30 bg-base-surface p-6">
            <h2 className="text-sm font-semibold text-ink-primary">{run.dataset_type === 'vendors' && !report?.transactions ? 'Next: upload transactions' : 'Next step'}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-muted">{nextStep}</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link to="/ingestion?type=transactions" className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-base-bg hover:bg-accent-dim">Upload transactions</Link>
              <Link to="/dashboard" className="rounded-md border border-base-border px-4 py-2.5 text-sm text-ink-primary hover:bg-base-surface2">Open workspace overview</Link>
            </div>
          </section>
        </div>
      </div>
    )
  }

  const metrics = [
    ['Transactions analyzed', report?.transactions ?? run.rows_received],
    ['Total transaction value', currency(report?.total_spend)],
    ['Risk alerts', report?.anomalies ?? run.anomalies_found],
    ['High risk', report?.high_risk_anomalies ?? 0],
  ]
  return (
    <div className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-accent">Analysis complete</p>
            <h1 className="mt-2 font-display text-2xl font-semibold text-ink-primary">Your finance report</h1>
            <p className="mt-1 text-sm text-ink-muted">{run.filename} · {new Date(run.created_at).toLocaleString()}</p>
          </div>
          <Link to="/ingestion" className="rounded-md border border-base-border px-4 py-2 text-sm text-ink-primary hover:bg-base-surface">Upload another file</Link>
        </div>

        <div className="mt-7 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {metrics.map(([label, value]) => <div key={label} className="rounded-lg border border-base-border bg-base-surface p-5">
            <p className="text-xs text-ink-muted">{label}</p><p className="mt-2 font-display text-2xl font-semibold text-ink-primary">{Number.isFinite(value) ? value.toLocaleString() : value}</p>
          </div>)}
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <section className="rounded-lg border border-base-border bg-base-surface">
            <div className="border-b border-base-border px-5 py-4">
              <h2 className="text-sm font-medium text-ink-primary">Flagged transactions</h2>
              <p className="mt-1 text-xs text-ink-faint">Ranked by risk score. Open a record to see evidence and investigation tools.</p>
            </div>
            <div className="divide-y divide-base-border">
              {(report?.top_anomalies || []).map((item) => <Link key={item.id} to={`/investigate/${item.id}`} className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-base-surface2">
                <div className="min-w-0"><p className="truncate text-sm font-medium text-ink-primary">{item.type === 'duplicate_invoice' ? 'Possible duplicate invoice' : 'Unusual transaction'} · {item.transaction_id}</p>
                  <p className="mt-1 truncate text-xs text-ink-faint">{(item.signals || []).join(' · ') || 'Review transaction evidence'}</p></div>
                <span className={`shrink-0 rounded px-2 py-1 font-mono text-xs ${item.risk_score >= 70 ? 'bg-risk-high/10 text-risk-high' : 'bg-base-bg text-ink-muted'}`}>{item.risk_score}/100</span>
              </Link>)}
              {(!report?.top_anomalies || report.top_anomalies.length === 0) && <p className="px-5 py-8 text-sm text-ink-faint">No anomalies were flagged in this scan.</p>}
            </div>
          </section>
          <aside className="space-y-4">
            <section className="rounded-lg border border-base-border bg-base-surface p-5">
              <h2 className="text-sm font-medium text-ink-primary">Reports</h2>
              <div className="mt-3 space-y-1">
                {[
                  ['/anomalies', 'Risk alerts', report?.anomalies ?? 0],
                  ['/budgets', 'Budget analysis', report?.budgets ?? 0],
                  ['/receivables', 'Receivables', report?.receivables ?? 0],
                  ['/cashflow', 'Cash flow forecast', 'View'],
                ].map(([href, label, count]) => <Link key={href} to={href} className="flex items-center justify-between rounded px-2 py-2.5 text-sm text-ink-muted hover:bg-base-surface2 hover:text-ink-primary"><span>{label}</span><span className="font-mono text-xs text-ink-faint">{count}</span></Link>)}
              </div>
            </section>
            <section className="rounded-lg border border-base-border bg-base-surface p-5">
              <h2 className="text-sm font-medium text-ink-primary">Scan summary</h2>
              <p className="mt-3 text-sm text-ink-muted">{report?.duplicate_invoices ?? 0} possible duplicate invoices</p>
              <p className="mt-1 text-sm text-ink-muted">{report?.ml_flags ?? 0} model anomaly flags</p>
              <p className="mt-3 text-xs leading-5 text-ink-faint">Flags are decision support. Review the supporting records before taking action.</p>
            </section>
          </aside>
        </div>
      </div>
    </div>
  )
}
