import { NavLink, Outlet } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/anomalies', label: 'Risk Alerts' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/receivables', label: 'Receivables' },
  { to: '/cashflow', label: 'Cash Flow' },
  { to: '/assistant', label: 'Ask FinGuard' },
]

export default function Layout() {
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
        <div className="px-5 py-4 border-t border-base-border text-[11px] text-ink-faint">
          Synthetic demo data — not real financial records.
        </div>
      </aside>
      <main className="flex-1 bg-base-bg">
        <Outlet />
      </main>
    </div>
  )
}
