const WIDTH = 280
const HEIGHT = 130
const PAD_TOP = 14
const PAD_BOTTOM = 10
const PAD_LEFT = 32   // wide enough for y-axis labels
const PAD_RIGHT = 4

/**
 * Every value here is <= 0 (0 is the unreachable ideal; see
 * models/evaluate.py's display_score for why). Bars hang downward from a
 * zero baseline at the top, so "shorter bar = better" reads the same way
 * a golfer reads a scorecard -- the explicit "0 = best" label and arrow
 * exist because that's not the default assumption for a bar chart.
 *
 * Note: the arrow below is the literal character, not a \u escape -- bare
 * JSX text (including inside an SVG <text>) gets no escape processing,
 * only actual JS string literals do.
 */
export function BarChart({ label, values, labels, color = 'var(--accent)' }) {
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

  const plotWidth = WIDTH - PAD_LEFT - PAD_RIGHT
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM

  // Round the axis max to the nearest even integer for clean tick values
  const maxAbsRaw = Math.max(...values.map((v) => Math.abs(v)), 1e-9)
  const axisMax = Math.ceil(maxAbsRaw / 2) * 2   // round up to next even number
  const barWidth = plotWidth / values.length

  // 3 evenly spaced ticks: 0, -axisMax/2, -axisMax
  const ticks = [0, -(axisMax / 2), -axisMax]

  const toY = (v) => PAD_TOP + (Math.abs(v) / axisMax) * plotHeight

  return (
    <div className="chart-block">
      <div className="chart-title">
        <span>{label}</span>
      </div>
      <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none">
        {/* y-axis ticks and grid lines */}
        {ticks.map((tick) => {
          const y = toY(tick)
          return (
            <g key={tick}>
              <line
                x1={PAD_LEFT - 3} y1={y}
                x2={WIDTH - PAD_RIGHT} y2={y}
                stroke="var(--graph-border)" strokeWidth="1"
                strokeDasharray={tick === 0 ? 'none' : '2,3'}
              />
              <text
                x={PAD_LEFT - 5} y={y + 3}
                fontSize="8" fill="var(--graph-text)"
                textAnchor="end"
              >
                {tick}
              </text>
            </g>
          )
        })}

        {/* y-axis spine */}
        <line
          x1={PAD_LEFT} y1={PAD_TOP}
          x2={PAD_LEFT} y2={HEIGHT - PAD_BOTTOM}
          stroke="var(--graph-border)" strokeWidth="1"
        />

        {/* "0 = best" annotation above the zero baseline */}
        <text x={PAD_LEFT + 2} y={PAD_TOP - 3} fontSize="8" fill="var(--graph-text)">0 = best ↑</text>

        {/* bars */}
        {values.map((v, i) => {
          const barHeight = (Math.abs(v) / axisMax) * plotHeight
          const x = PAD_LEFT + i * barWidth
          return (
            <rect
              key={i}
              x={x + 1}
              y={PAD_TOP}
              width={Math.max(1, barWidth - 2)}
              height={barHeight}
              fill={color}
              opacity={i === values.length - 1 ? 1 : 0.6}
            >
              <title>{labels?.[i] ? `${labels[i]}: ${v.toFixed(3)}` : v.toFixed(3)}</title>
            </rect>
          )
        })}
      </svg>
    </div>
  )
}
