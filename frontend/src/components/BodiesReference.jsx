export function BodiesReference({ bodies }) {
  const entries = Object.entries(bodies).filter(([key]) => key !== 'kepler_third_law_tolerance')
  if (entries.length === 0) return null

  return (
    <div className="panel">
      <h2>Orbital data &amp; tolerances</h2>
      <div className="families-legend">
        {entries.map(([name, info]) => (
          <div key={name}>
            {name}: a={info.a_au} AU, e={info.e}{' '}
            {info.role === 'calibration'
              ? `\u2014 observed precession ${info.observed_precession}″/cy (fit target)`
              : `\u2014 tolerance ${info.precession_tolerance}″/cy`}
          </div>
        ))}
        <div>Kepler's third law tolerance: {bodies.kepler_third_law_tolerance}</div>
      </div>
    </div>
  )
}
