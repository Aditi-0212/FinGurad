export default function StatCard({ label, value, sublabel, tone = 'default' }) {
  const toneClass = {
    default: 'text-ink-primary',
    good: 'text-risk-low',
    warn: 'text-risk-medium',
    bad: 'text-risk-high',
  }[tone]

  return (
    <div className="bg-base-surface border border-base-border rounded-lg px-5 py-4">
      <p className="text-[11px] uppercase tracking-wide text-ink-faint">{label}</p>
      <p className={`mt-1.5 text-2xl font-mono font-semibold ${toneClass}`}>{value}</p>
      {sublabel && <p className="mt-1 text-xs text-ink-muted">{sublabel}</p>}
    </div>
  )
}
