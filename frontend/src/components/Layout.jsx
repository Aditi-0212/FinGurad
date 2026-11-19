import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import api from '../api/client'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/anomalies', label: 'Risk Alerts' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/receivables', label: 'Receivables' },
  { to: '/cashflow', label: 'Cash Flow' },
  { to: '/assistant', label: 'Ask FinGuard' },
  { to: '/ingestion', label: 'Upload Data' },
]

export default function Layout({ identity, onLogout }) {
  const location = useLocation()
  const [workspace, setWorkspace] = useState(null)
  const [workspaceError, setWorkspaceError] = useState(false)

  useEffect(() => {
    let active = true
    api.getWorkspaceSummary()
      .then((summary) => { if (active) { setWorkspace(summary); setWorkspaceError(false) } })
      .catch(() => { if (active) setWorkspaceError(true) })
    return () => { active = false }
  }, [location.pathname])

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-base-border bg-base-surface flex flex-col">
        <div className="px-5 py-6 border-b border-base-border">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-accent-soft border border-accent/40 flex items-center justify-center">
              <span className="font-mono text-accent text-xs font-semibold">FG</span>
            </div>
            <span className="font-display font-semibold tracking-tight text-ink-primary">FinGuard AI</span>
          </div>
          <p className="mt-1 text-[11px] text-ink-faint tracking-wide uppercase">Finance Controller</p>
          <p className="mt-3 truncate text-xs font-medium text-accent" title={identity?.company_name}>{identity?.company_name}</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-accent-soft text-accent font-medium'
                    : 'text-ink-muted hover:text-ink-primary hover:bg-base-surface2'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-base-border px-4 py-4">
          <p className="mb-2 text-[10px] uppercase tracking-wider text-ink-faint">This workspace’s data</p>
          {workspace && <>
            <p className="text-[11px] text-ink-muted">{workspace.counts.transactions.toLocaleString()} transactions · {workspace.counts.vendors.toLocaleString()} vendors</p>
            <p className="mt-0.5 text-[11px] text-ink-muted">{workspace.counts.budgets.toLocaleString()} budgets · {workspace.counts.receivables.toLocaleString()} receivables</p>
            {workspace.latest_import && <p className="mt-2 truncate text-[10px] text-ink-faint" title={workspace.latest_import.filename}>Latest import: {workspace.latest_import.filename}</p>}
          </>}
          {workspaceError && <p className="text-[10px] text-risk-high">Workspace data could not be checked</p>}
          {!workspace && !workspaceError && <p className="text-[10px] text-ink-faint">Checking saved data…</p>}
        </div>
        <div className="border-t border-base-border px-4 py-4">
          <p className="truncate text-xs text-ink-primary">{identity?.name}</p>
          <p className="truncate text-[10px] text-ink-faint">{identity?.email}</p>
          <button onClick={onLogout} className="mt-3 text-xs text-ink-muted hover:text-risk-high">Sign out</button>
        </div>
      </aside>
      <main className="flex-1 bg-base-bg">
        <Outlet />
      </main>
    </div>
  )
}
