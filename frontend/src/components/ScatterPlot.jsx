const WIDTH = 460
const HEIGHT = 300
const PAD = 30

function scaleFactory(values, size, pad) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  return (v) => pad + ((v - min) / range) * (size - 2 * pad)
}

export function ScatterPlot({ dataset, curveX, curveY, formula }) {
  if (!dataset) {
    return <div className="empty-state">Run to generate data.</div>
  }

  const allX = [...dataset.x_train, ...dataset.x_test, ...(curveX ?? [])]
  const allY = [
    ...dataset.y_train,
    ...dataset.y_test,
    ...((curveY ?? []).filter((v) => Number.isFinite(v))),
  ]

  const scaleX = scaleFactory(allX, WIDTH, PAD)
  // y is inverted: data-up means svg-up, i.e. smaller pixel y
  const yMin = Math.min(...allY)
  const yMax = Math.max(...allY)
  const yRange = yMax - yMin || 1
  const scaleY = (v) => HEIGHT - PAD - ((v - yMin) / yRange) * (HEIGHT - 2 * PAD)

  const curvePoints =
    curveX && curveY
      ? curveX
          .map((x, i) => [x, curveY[i]])
          .filter(([, y]) => Number.isFinite(y))
          .map(([x, y]) => `${scaleX(x)},${scaleY(y)}`)
          .join(' ')
      : ''

  return (
    <div className="scatter-plot">
      <svg width="100%" viewBox={`0 0 ${WIDTH} ${HEIGHT}`}>
        {dataset.x_train.map((x, i) => (
          <circle key={`tr-${i}`} cx={scaleX(x)} cy={scaleY(dataset.y_train[i])} r="3" fill="var(--teal)" opacity="0.85" />
        ))}
        {dataset.x_test.map((x, i) => (
          <circle
            key={`te-${i}`}
            cx={scaleX(x)}
            cy={scaleY(dataset.y_test[i])}
            r="3.5"
            fill="none"
            stroke="var(--text-dim)"
            strokeWidth="1.2"
          />
        ))}
        {curvePoints && <polyline points={curvePoints} fill="none" stroke="var(--accent)" strokeWidth="2" />}
      </svg>
      {formula && <div className="formula">{formula}</div>}
    </div>
  )
}
