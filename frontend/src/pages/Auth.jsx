import { useState } from 'react'
import api from '../api/client'

export default function Auth({ onAuthenticated }) {
  const [mode, setMode] = useState('register')
  const [companyName, setCompanyName] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    if (pending) return
    setPending(true)
    setError('')
    try {
      const identity = mode === 'register'
        ? await api.register({ company_name: companyName, name, email, password })
        : await api.login({ email, password })
      localStorage.setItem('finguard_token', identity.access_token)
      localStorage.setItem('finguard_identity', JSON.stringify(identity))
      window.history.replaceState(null, '', '/')
      onAuthenticated(identity)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Could not connect to FinGuard')
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="min-h-screen bg-base-bg px-5 py-12 text-ink-primary">
      <div className="mx-auto grid max-w-5xl overflow-hidden rounded-2xl border border-base-border bg-base-surface md:grid-cols-[1fr_0.9fr]">
        <section className="flex flex-col justify-between bg-base-surface2 p-8 md:p-10">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/40 bg-accent-soft font-mono text-sm font-semibold text-accent">FG</div>
              <div><p className="font-display font-semibold">FinGuard AI</p><p className="text-[10px] uppercase tracking-widest text-ink-faint">Finance controller</p></div>
            </div>
            <h1 className="mt-16 max-w-md font-display text-3xl font-semibold leading-tight">Your company data. Your finance workspace.</h1>
            <p className="mt-4 max-w-md text-sm leading-6 text-ink-muted">Create a workspace for your organization. Financial records and reports are stored separately for each company.</p>
          </div>
          <p className="mt-16 text-xs text-ink-faint">New workspaces start empty. Upload your own CSV to see analysis.</p>
        </section>
        <section className="p-8 md:p-10">
          <div className="mb-7 flex gap-5 border-b border-base-border">
            {['register', 'login'].map((tab) => <button key={tab} type="button" onClick={() => { setMode(tab); setError('') }} className={`border-b-2 pb-3 text-sm capitalize ${mode === tab ? 'border-accent text-accent' : 'border-transparent text-ink-muted'}`}>{tab === 'register' ? 'Create workspace' : 'Sign in'}</button>)}
          </div>
          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && <>
              <label className="block text-xs text-ink-muted">Company name<input required minLength={2} maxLength={160} value={companyName} onChange={(e) => setCompanyName(e.target.value)} className="mt-1.5 block w-full rounded-md border border-base-border bg-base-bg px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent" placeholder="Acme Finance" /></label>
              <label className="block text-xs text-ink-muted">Your name<input required minLength={2} maxLength={120} value={name} onChange={(e) => setName(e.target.value)} className="mt-1.5 block w-full rounded-md border border-base-border bg-base-bg px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent" placeholder="Finance manager" /></label>
            </>}
            <label className="block text-xs text-ink-muted">Work email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5 block w-full rounded-md border border-base-border bg-base-bg px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent" placeholder="you@company.com" /></label>
            <label className="block text-xs text-ink-muted">Password<input required type="password" minLength={mode === 'register' ? 10 : 1} value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5 block w-full rounded-md border border-base-border bg-base-bg px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent" placeholder={mode === 'register' ? 'At least 10 characters' : 'Your password'} /></label>
            {error && <p role="alert" className="text-sm text-risk-high">{error}</p>}
            <button disabled={pending} className="w-full rounded-md bg-accent px-4 py-3 text-sm font-semibold text-base-bg hover:bg-accent-dim disabled:opacity-50">{pending ? 'Please wait…' : mode === 'register' ? 'Create isolated workspace' : 'Sign in to workspace'}</button>
          </form>
        </section>
      </div>
    </main>
  )
}
