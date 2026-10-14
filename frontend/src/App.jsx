import { useEffect, useRef, useState } from 'react'
import { MDLClient } from './api'
import { ControlPanel } from './components/ControlPanel'
import { ConstraintTable } from './components/ConstraintTable'
import { MetricsChart } from './components/MetricsChart'
import { BarChart } from './components/BarChart'
import { IterationLog } from './components/IterationLog'
import { FamiliesLegend } from './components/FamiliesLegend'
import { BodiesReference } from './components/BodiesReference'
import { KnowledgeBase } from './components/KnowledgeBase'

function App() {
  const [families, setFamilies] = useState({})
  const [bodies, setBodies] = useState({})
  const [knowledgeBase, setKnowledgeBase] = useState(null)
  const [loadError, setLoadError] = useState(null)

  const [params, setParams] = useState({
    starting_family: 'hall_law',
    max_iterations: 10,
  })

  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState(null)
  const [history, setHistory] = useState([])
  const [formula, setFormula] = useState('')
  const [note, setNote] = useState('')
  const [precessionChecks, setPrecessionChecks] = useState([])
  const [keplerChecks, setKeplerChecks] = useState([])
  const [bestResult, setBestResult] = useState(null)

  const sourceRef = useRef(null)

  useEffect(() => {
    Promise.all([MDLClient.getFamilies(), MDLClient.getBodies(), MDLClient.getKnowledgeBase()])
      .then(([f, b, kb]) => {
        setFamilies(f)
        setBodies(b)
        setKnowledgeBase(kb)
      })
      .catch((e) => setLoadError(e.message))
    return () => sourceRef.current?.close()
  }, [])

  function setParam(key, value) {
    setParams((prev) => ({ ...prev, [key]: value }))
  }

  function handleRun() {
    sourceRef.current?.close()
    setRunning(true)
    setRunError(null)
    setHistory([])
    setFormula('')
    setNote('')
    setPrecessionChecks([])
    setKeplerChecks([])
    setBestResult(null)

    sourceRef.current = MDLClient.runStream(params, {
      onIteration: (payload) => {
        setHistory((prev) => [
          ...prev,
          { iteration: payload.iteration, config: payload.config, metrics: payload.metrics, reflection: payload.reflection },
        ])
        setFormula(payload.formula)
        setNote(payload.note)
        setPrecessionChecks(payload.precession_checks)
        setKeplerChecks(payload.kepler_checks)
        setBestResult(payload.best_result)
      },
      onDone: () => setRunning(false),
      onError: (e) => {
        setRunError(e.message)
        setRunning(false)
      },
    })
  }

  const seriesFor = (key) => history.map((h) => h.metrics[key])
  const latestFamily = history.length > 0 ? history[history.length - 1].config.family : ''

  return (
    <div className="app">
      <header className="app-header">
        <h1>Pre-1900 Gravity Model Selection</h1>
        <span className="subtitle">fit Mercury, survive Venus/Earth/Mars/Moon and Kepler's third law — or don't</span>
      </header>

      <div className="layout">
        <div>
          <ControlPanel
            params={params}
            setParam={setParam}
            families={families}
            onRun={handleRun}
            running={running}
            error={runError}
            completedIterations={history.length}
            maxIterations={params.max_iterations}
          />
          {loadError && <div className="status-line error">{loadError}</div>}
          <BodiesReference bodies={bodies} />
          <KnowledgeBase knowledgeBase={knowledgeBase} />
          <FamiliesLegend families={families} />
        </div>

        <div>
          {bestResult && (
            <div className="panel">
              <h2>Best result — {bestResult.family} (iteration {bestResult.iteration})</h2>
              <ConstraintTable
                formula={bestResult.formula}
                note={bestResult.note}
                precessionChecks={bestResult.precession_checks}
                keplerChecks={bestResult.kepler_checks}
              />
            </div>
          )}
          <div className="panel">
            <h2>Latest attempt {latestFamily ? `— ${latestFamily}` : ''}</h2>
            <ConstraintTable formula={formula} note={note} precessionChecks={precessionChecks} keplerChecks={keplerChecks} />
          </div>
          <div className="panel">
            <h2>Metrics over iterations</h2>
            <MetricsChart label="accuracy penalty (0 = passes everything)" values={seriesFor('accuracy_penalty')} color="var(--danger)" />
            <MetricsChart label="complexity score" values={seriesFor('complexity_score')} color="var(--teal)" />
            <BarChart
              label="overall score (log-compressed for display)"
              values={seriesFor('display_score')}
              labels={history.map((h) => h.config.family)}
              color="var(--accent)"
            />
          </div>
          <div className="panel">
            <h2>Iteration log</h2>
            <IterationLog history={history} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
