export function KnowledgeBase({ knowledgeBase }) {
  if (!knowledgeBase || !knowledgeBase.laws) return null

  return (
    <div className="panel">
      <h2>Known physics &amp; math (pre-1900 input)</h2>
      <div className="families-legend">
        {knowledgeBase.laws.map((law) => (
          <div key={law.name}>
            {law.year_established}: {law.name} ({law.mathematical_form})
          </div>
        ))}
        {knowledgeBase.math_tools.map((tool) => (
          <div key={tool.name}>
            {tool.year_available}: {tool.name}
          </div>
        ))}
      </div>
    </div>
  )
}
