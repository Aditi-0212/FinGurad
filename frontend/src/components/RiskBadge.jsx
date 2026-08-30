const STYLES = {
  LOW: 'bg-risk-low/10 text-risk-low border-risk-low/30',
  MEDIUM: 'bg-risk-medium/10 text-risk-medium border-risk-medium/30',
  HIGH: 'bg-risk-high/10 text-risk-high border-risk-high/30',
}

export default function RiskBadge({ level, className = '' }) {
  const style = STYLES[level] || STYLES.LOW
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[11px] font-mono font-medium tracking-wide ${style} ${className}`}>
      {level}
    </span>
  )
}
