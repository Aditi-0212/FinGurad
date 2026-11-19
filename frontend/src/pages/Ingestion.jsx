import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

const FILE_FIELDS = [
  ['transactions', 'Transactions', true, 'Required for risk analysis', 'transaction_id, date, vendor_id, vendor_name, department, category, amount, payment_method, invoice_id'],
  ['vendors', 'Vendors', false, 'Optional · enriches vendor risk profiles', 'vendor_id, vendor_name, vendor_age, industry, risk_level, total_transactions, average_transaction'],
  ['budgets', 'Budgets', false, 'Optional · adds budget monitoring', 'department, month, budget, actual_spending'],
  ['receivables', 'Receivables', false, 'Optional · adds collections and cash flow reports', 'invoice_id, customer, invoice_date, due_date, amount, payment_status'],
]

// Keep selected File objects while the user moves between SPA tabs.
let uploadDraft = {}

export default function Ingestion() {
  const [files, setFiles] = useState(() => uploadDraft)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const submit = async (event) => {
    event.preventDefault()
    if (!files.transactions || loading) {
      setError('Choose a transactions CSV to generate the analysis report.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await api.uploadBundle(files)
      uploadDraft = {}
      setFiles({})
      navigate(`/analysis/${result.run_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Upload failed')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-6 py-10 md:px-10">
      <div className="mx-auto max-w-4xl">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-accent">FinGuard · Secure company workspace</p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-ink-primary">Upload finance data</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-ink-muted">Add a transaction file to run the analysis. Attach vendor, budget, or receivables files in the same upload if you have them. FinGuard imports the files together and opens one report when processing finishes.</p>

        <form onSubmit={submit} className="mt-7 rounded-xl border border-base-border bg-base-surface p-5 md:p-7">
          <div className="grid gap-4 md:grid-cols-2">
            {FILE_FIELDS.map(([key, label, required, description, columns]) => (
              <label key={key} className={`block rounded-lg border p-4 ${required ? 'border-accent/40 bg-accent-soft/30' : 'border-base-border bg-base-bg'}`}>
                <span className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-ink-primary">{label}{required && <span className="ml-1 text-risk-high">*</span>}</span>
                  <span className="text-[10px] text-ink-faint">{required ? 'Required' : 'Optional'}</span>
                </span>
                <span className="mt-1 block text-xs text-ink-muted">{description}</span>
                <span className="mt-3 flex min-h-10 cursor-pointer items-center rounded-md border border-base-border bg-base-surface px-3 text-xs text-ink-muted hover:border-accent/50">
                  <span className="truncate">{files[key]?.name || 'Choose CSV file'}</span>
                </span>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  required={required}
                  onChange={(e) => setFiles((current) => {
                    uploadDraft = { ...current, [key]: e.target.files?.[0] || null }
                    return uploadDraft
                  })}
                  className="sr-only"
                />
                <span className="mt-2 block break-words font-mono text-[10px] leading-4 text-ink-faint">{columns}</span>
              </label>
            ))}
          </div>

          <div className="mt-5 rounded-md border border-base-border bg-base-bg px-4 py-3 text-xs leading-5 text-ink-faint">
            Transactions can be analyzed on their own. Missing vendor profiles are created automatically; if a vendor CSV is included, it is imported first so vendor IDs can be matched.
          </div>
          {error && <p role="alert" className="mt-4 text-sm text-risk-high">{error}</p>}
          <button disabled={!files.transactions || loading} className="mt-5 w-full rounded-md bg-accent px-4 py-3 text-sm font-semibold text-base-bg hover:bg-accent-dim disabled:cursor-not-allowed disabled:opacity-50">
            {loading ? 'Uploading files…' : 'Upload and analyze'}
          </button>
          <p className="mt-3 text-center text-[11px] text-ink-faint">Up to 10 MB and 50,000 rows per file. Each company workspace is isolated.</p>
        </form>
      </div>
    </div>
  )
}
