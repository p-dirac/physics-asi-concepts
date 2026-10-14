export function FamiliesLegend({ families }) {
  const entries = Object.entries(families)
  if (entries.length === 0) return null

  return (
    <div className="panel">
      <h2>Candidate families</h2>
      <div className="families-legend">
        {entries.map(([name, info]) => (
          <div key={name}>
            {name}: {info.formula} (struct={info.structural_cost}, params={info.num_params})
            {info.note && ` \u2014 ${info.note}`}
          </div>
        ))}
      </div>
    </div>
  )
}
