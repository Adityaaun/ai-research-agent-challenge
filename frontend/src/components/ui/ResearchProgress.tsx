import { useEffect, useState } from 'react'
import { CheckCircle2, Circle, Loader2 } from 'lucide-react'
import { API_BASE } from "../../config"

interface ResearchProgressProps {
  question: string
  workspaceId?: string
  onComplete: (data: any) => void
}

const STEPS = [
  "Planning",
  "Retrieving evidence",
  "Reranking",
  "Extracting claims",
  "Checking contradictions",
  "Calculating confidence",
  "Writing report"
]

export function ResearchProgress({ question, workspaceId, onComplete }: ResearchProgressProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [messages, setMessages] = useState<string[]>([])
  
  useEffect(() => {
    if (!question) return
    
    // Connect to SSE endpoint
    const url = new URL(`${API_BASE}/api/v1/research/start`)
    url.searchParams.append('question', question)
    if (workspaceId) {
      url.searchParams.append('workspace_id', workspaceId)
    }
    
    const eventSource = new EventSource(url.toString())
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.status === 'progress') {
        const stepIdx = STEPS.indexOf(data.step)
        if (stepIdx !== -1) {
          setCurrentStepIndex(stepIdx)
        }
        if (data.message) {
          setMessages(prev => [...prev, data.message])
        }
      } else if (data.status === 'complete') {
        setCurrentStepIndex(STEPS.length)
        onComplete(data)
        eventSource.close()
      }
    }
    
    eventSource.onerror = () => {
      eventSource.close()
    }
    
    return () => {
      eventSource.close()
    }
  }, [question, workspaceId, onComplete])

  return (
    <div className="bg-card border rounded-xl p-6 shadow-sm space-y-6">
      <div>
        <h3 className="text-xl font-semibold tracking-tight">Researching...</h3>
        <p className="text-muted-foreground text-sm mt-1">"{question}"</p>
      </div>
      
      <div className="space-y-4">
        {STEPS.map((step, idx) => {
          const isCompleted = idx < currentStepIndex
          const isCurrent = idx === currentStepIndex
          
          return (
            <div key={step} className="flex items-center space-x-3">
              {isCompleted ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : isCurrent ? (
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              ) : (
                <Circle className="w-5 h-5 text-muted-foreground/30" />
              )}
              <span className={isCurrent ? "font-medium text-foreground" : isCompleted ? "text-muted-foreground line-through decoration-muted-foreground/30" : "text-muted-foreground"}>
                {step}
              </span>
            </div>
          )
        })}
      </div>
      
      <div className="mt-6 pt-6 border-t border-border/50">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Live Logs</h4>
        <div className="h-32 overflow-y-auto rounded bg-background/50 p-3 font-mono text-xs text-muted-foreground flex flex-col justify-end">
          {messages.slice(-5).map((msg, i) => (
            <div key={i} className="mb-1">{">"} {msg}</div>
          ))}
        </div>
      </div>
    </div>
  )
}
