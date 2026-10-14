const WIDTH = 260
const HEIGHT = 56
const PAD = 4

function pointsFor(values, min, range) {
  return values.map((v, i) => {
    const x = PAD + (i / Math.max(1, values.length - 1)) * (WIDTH - 2 * PAD)
    const y = HEIGHT - PAD - ((v - min) / range) * (HEIGHT - 2 * PAD)
    return [x, y]
  })
}

export function MetricsChart({ label, values, color = 'var(--accent)' }) {
  if (!values || values.length === 0) {
    return (
      <div className="chart-block">
        <div className="chart-title">
          <span>{label}</span>
        </div>
        <div className="empty-state">no data yet</div>
      </div>
    )
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const points = pointsFor(values, min, range)

  return (
    <div className="chart-block">
      <div className="chart-title">
        <span>{label}</span>
      </div>
      <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none">
        <polyline
          points={points.map(([x, y]) => `${x},${y}`).join(' ')}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
        />
        {points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="2" fill={color} />
        ))}
      </svg>
    </div>
  )
}
