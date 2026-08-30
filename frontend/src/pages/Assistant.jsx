import { useState } from 'react'
import api from '../api/client'

const SUGGESTIONS = [
  'Which departments exceeded their budgets?',
  'What are our highest-value overdue receivables?',
  'Which transactions have the highest risk?',
  'How is our cash position expected to change?',
]

export default function Assistant() {
  const [history, setHistory] = useState([])
  const [question, setQuestion] = useState('')
  const [pending, setPending] = useState(false)

  const ask = (q) => {
    const text = q ?? question
    if (!text.trim() || pending) return
    setHistory((h) => [...h, { role: 'user', text }])
    setQuestion('')
    setPending(true)
    api
      .queryAssistant(text)
      .then((res) => {
        setHistory((h) => [...h, { role: 'assistant', text: res.answer, toolCalls: res.tool_calls_made }])
      })
      .catch((e) => {
        const detail = e.response?.data?.detail || e.message || 'Assistant request failed — check GROQ_API_KEY is set on the backend.'
        setHistory((h) => [...h, { role: 'assistant', text: detail, isError: true }])
      })
      .finally(() => setPending(false))
  }

  return (
    <div className="p-8 max-w-3xl mx-auto flex flex-col h-screen">
      <h1 className="font-display text-xl font-semibold text-ink-primary mb-1">Ask FinGuard</h1>
      <p className="text-sm text-ink-muted mb-6">Ask questions about the company's real financial data.</p>

      {history.length === 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => ask(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-base-border text-ink-muted hover:text-accent hover:border-accent/40 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {history.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-accent text-base-bg'
                  : msg.isError
                    ? 'bg-risk-high/10 border border-risk-high/30 text-risk-high'
                    : 'bg-base-surface border border-base-border text-ink-primary'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.toolCalls?.length > 0 && (
                <p className="mt-2 text-[10px] text-ink-faint font-mono">
                  data: {msg.toolCalls.map((t) => t.split('(')[0]).join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}
        {pending && <div className="text-sm text-ink-faint">Thinking…</div>}
      </div>

      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder="Ask about budgets, receivables, risk, cash flow…"
          className="flex-1 bg-base-surface border border-base-border rounded-md px-4 py-2.5 text-sm text-ink-primary placeholder:text-ink-faint focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <button
          onClick={() => ask()}
          disabled={pending}
          className="px-4 py-2.5 bg-accent text-base-bg text-sm font-medium rounded-md hover:bg-accent-dim transition-colors disabled:opacity-50"
        >
          Ask
        </button>
      </div>
    </div>
  )
}
