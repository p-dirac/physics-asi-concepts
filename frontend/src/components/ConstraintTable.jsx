function formatNumber(v) {
  if (!Number.isFinite(v)) return '—'
  const abs = Math.abs(v)
  if (abs !== 0 && (abs < 0.001 || abs >= 100000)) return v.toExponential(2)
  return v.toFixed(abs < 10 ? 3 : 2)
}

function CheckRow({ label, unit, check }) {
  const passed = check.normalized_excess === 0
  return (
    <div className="constraint-row">
      <span className="constraint-label">{label}</span>
      <span className="constraint-value">
        {formatNumber(check.predicted)} {unit}
      </span>
      <span className="constraint-tolerance">tol {formatNumber(check.tolerance)}</span>
      <span className={`constraint-verdict ${passed ? 'pass' : 'fail'}`}>
        {passed ? 'PASS' : `${formatNumber(check.normalized_excess)}\u00d7 over`}
      </span>
    </div>
  )
}

export function ConstraintTable({ formula, note, precessionChecks, keplerChecks }) {
  if (!precessionChecks || precessionChecks.length === 0) {
    return <div className="empty-state">Run to see how this family holds up against Venus, Earth, Mars, the Moon, and Kepler's third law.</div>
  }

  const bodyLabel = (b) => b.charAt(0).toUpperCase() + b.slice(1)

  return (
    <div className="constraint-table">
      {formula && <div className="formula">{formula}</div>}
      {note && <div className="family-note">{note}</div>}

      <div className="constraint-group-title">Precession (arcsec/century)</div>
      {precessionChecks.map((c) => (
        <CheckRow key={c.body} label={bodyLabel(c.body)} unit="″/cy" check={c} />
      ))}

      <div className="constraint-group-title">Kepler's third law (fractional deviation)</div>
      {keplerChecks.map((c) => (
        <CheckRow key={c.body} label={bodyLabel(c.body)} unit="" check={c} />
      ))}
    </div>
  )
}
