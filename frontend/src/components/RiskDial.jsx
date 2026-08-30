const riskColor = (score) => {
  if (score >= 70) return '#F87171'
  if (score >= 40) return '#F59E0B'
  return '#34D399'
}

const riskLabel = (score) => {
  if (score >= 70) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  return 'LOW'
}

export default function RiskDial({ score }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const pct = Math.max(0, Math.min(100, score)) / 100
  const dashOffset = circumference * (1 - pct)
  const color = riskColor(score)

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 128 128" className="w-full h-full -rotate-90">
          <circle cx="64" cy="64" r={radius} fill="none" stroke="#232C36" strokeWidth="10" />
          <circle
            cx="64"
            cy="64"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-3xl font-semibold" style={{ color }}>
            {score}
          </span>
          <span className="text-[10px] text-ink-faint tracking-wide">/ 100</span>
        </div>
      </div>
      <span
        className="mt-2 font-mono text-xs font-semibold tracking-widest px-2 py-0.5 rounded border"
        style={{ color, borderColor: `${color}4D`, backgroundColor: `${color}1A` }}
      >
        {riskLabel(score)} RISK
      </span>
    </div>
  )
}
