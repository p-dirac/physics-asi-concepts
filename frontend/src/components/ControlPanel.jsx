export function ControlPanel({ params, setParam, families, onRun, running, error, completedIterations, maxIterations }) {
  return (
    <div className="panel">
      <h2>Run configuration</h2>

      <div className="field">
        <label htmlFor="starting-family">Starting family</label>
        <select
          id="starting-family"
          value={params.starting_family}
          onChange={(e) => setParam('starting_family', e.target.value)}
          disabled={running}
        >
          {Object.keys(families).map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
        <div className="hint">Mercury calibration is exact by construction — what varies is whether the fit survives Venus/Earth/Mars/Moon too.</div>
      </div>

      <div className="field">
        <label htmlFor="max-iterations">Max iterations</label>
        <input
          id="max-iterations"
          type="number"
          min="1"
          max="15"
          value={params.max_iterations}
          onChange={(e) => setParam('max_iterations', Number(e.target.value))}
          disabled={running}
        />
      </div>

      <button className="run-button" onClick={onRun} disabled={running}>
        {running ? `Running… (${completedIterations}/${maxIterations})` : 'Run model selection'}
      </button>

      {error && <div className="status-line error">{error}</div>}
      {!error && running && (
        <div className="status-line">Streaming live — each round checks one family against Mercury, Venus, Earth, Mars, the Moon, and Kepler's third law.</div>
      )}
    </div>
  )
}
