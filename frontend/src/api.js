const BASE_URL = 'http://localhost:8001'

export class MDLClient {
  static async getFamilies() {
    const res = await fetch(`${BASE_URL}/api/families`)
    if (!res.ok) throw new Error(`GET /api/families failed: ${res.status}`)
    return res.json()
  }

  static async getBodies() {
    const res = await fetch(`${BASE_URL}/api/bodies`)
    if (!res.ok) throw new Error(`GET /api/bodies failed: ${res.status}`)
    return res.json()
  }

  static async getKnowledgeBase() {
    const res = await fetch(`${BASE_URL}/api/knowledge_base`)
    if (!res.ok) throw new Error(`GET /api/knowledge_base failed: ${res.status}`)
    return res.json()
  }

  /**
   * Streams a run via Server-Sent Events -- one 'iteration' event per
   * completed round (each carrying that round's full constraint
   * breakdown), then 'done'.
   */
  static runStream(params, { onIteration, onDone, onError }) {
    const query = new URLSearchParams(params).toString()
    const source = new EventSource(`${BASE_URL}/api/run/stream?${query}`)

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data)
      if (payload.type === 'iteration') {
        onIteration(payload)
      } else if (payload.type === 'done') {
        source.close()
        onDone()
      }
    }

    source.onerror = () => {
      source.close()
      onError(new Error('Connection to /api/run/stream failed or was interrupted.'))
    }

    return source
  }
}
