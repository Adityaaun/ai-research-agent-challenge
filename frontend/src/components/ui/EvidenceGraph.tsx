import { useMemo } from 'react'
import ReactFlow, { Background, Controls, Position, type Edge, type Node } from 'reactflow'
import 'reactflow/dist/style.css'

interface EvidenceGraphProps {
  question: string
  claims: any[]
  evidence: any[]
}

export function EvidenceGraph({ question, claims, evidence }: EvidenceGraphProps) {
  const { nodes, edges } = useMemo(() => {
    const newNodes: Node[] = []
    const newEdges: Edge[] = []
    
    // 1. Root Question Node
    newNodes.push({
      id: 'q-root',
      type: 'input',
      data: { label: <div className="font-bold text-sm text-center px-2 py-1">Research Question<br/><span className="font-normal text-xs text-muted-foreground break-words whitespace-normal">{question}</span></div> },
      position: { x: 400, y: 50 },
      className: 'bg-primary/10 border-primary border-2 rounded-xl shadow-sm w-64',
      sourcePosition: Position.Bottom,
    })

    // 2. Claim Nodes
    claims.forEach((claim, i) => {
      const claimId = `c-${i}`
      newNodes.push({
        id: claimId,
        data: { label: <div className="text-sm font-medium">{claim.claim} <span className="block mt-1 text-xs text-primary">{claim.confidence}% Conf</span></div> },
        position: { x: 100 + (i * 300), y: 200 },
        className: 'bg-card border-2 border-border rounded-lg shadow-sm w-56',
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      })
      
      newEdges.push({
        id: `e-q-${claimId}`,
        source: 'q-root',
        target: claimId,
        animated: true,
        style: { stroke: 'hsl(var(--primary))' }
      })
      
      // 3. Evidence Nodes
      const processEvidence = (sourceIds: string[], type: 'support' | 'contradict') => {
        sourceIds?.forEach((sourceId, j) => {
          const evNodeId = `e-${i}-${j}-${type}`
          const sourceObj = evidence.find(e => `${e.metadata.source}_${e.metadata.chunk_index}` === sourceId)
          const sourceName = sourceObj ? sourceObj.metadata.source : sourceId
          
          if (!newNodes.find(n => n.id === evNodeId)) {
            newNodes.push({
              id: evNodeId,
              data: { label: <div className="text-xs font-mono">{sourceName}</div> },
              position: { x: 50 + (i * 300) + (j * 150), y: 350 },
              className: `rounded-md border p-2 w-32 ${type === 'support' ? 'bg-green-500/10 border-green-500/50' : 'bg-red-500/10 border-red-500/50'}`,
              targetPosition: Position.Top,
            })
          }
          
          newEdges.push({
            id: `edge-${claimId}-${evNodeId}`,
            source: claimId,
            target: evNodeId,
            label: type === 'support' ? 'Supports' : 'Contradicts',
            labelStyle: { fill: type === 'support' ? '#22c55e' : '#ef4444', fontSize: 10, fontWeight: 700 },
            style: { stroke: type === 'support' ? '#22c55e' : '#ef4444', strokeWidth: 2 },
            animated: type === 'contradict'
          })
        })
      }
      
      processEvidence(claim.supporting_source_ids, 'support')
      processEvidence(claim.contradicting_source_ids, 'contradict')
    })
    
    return { nodes: newNodes, edges: newEdges }
  }, [question, claims, evidence])

  return (
    <div className="w-full h-[500px] border border-border rounded-xl overflow-hidden bg-background/50">
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView
        attributionPosition="bottom-right"
        className="dark"
      >
        <Background color="#555" gap={16} />
        <Controls className="bg-background border-border fill-foreground" />
      </ReactFlow>
    </div>
  )
}
