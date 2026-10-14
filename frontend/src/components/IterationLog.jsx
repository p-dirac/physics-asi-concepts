export function IterationLog({ history }) {
  if (!history || history.length === 0) {
    return <div className="empty-state">Run the loop to see which families get tried, and why.</div>
  }

  return (
    <div className="iteration-log">
      {history.map((entry) => (
        <div className="iteration-row" key={entry.iteration}>
          <span className="idx">{entry.iteration}</span>
          <span className="reflection">{entry.reflection}</span>
          <span className="family">{entry.config.family}</span>
        </div>
      ))}
    </div>
  )
}
