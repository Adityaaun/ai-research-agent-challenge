import { useState } from 'react'
import { FileUpload } from './components/ui/FileUpload'
import { ResearchProgress } from './components/ui/ResearchProgress'
import { EvidenceGraph } from './components/ui/EvidenceGraph'
import { motion, AnimatePresence } from 'framer-motion'

function App() {
  const [question, setQuestion] = useState('')
  const [isResearching, setIsResearching] = useState(false)
  const [activeQuestion, setActiveQuestion] = useState('')
  const [report, setReport] = useState<string | null>(null)
  const [claims, setClaims] = useState<any[]>([])
  const [evidence, setEvidence] = useState<any[]>([])
  const [documents, setDocuments] = useState<any[]>([])

  const handleUploadSuccess = (doc: any) => {
    setDocuments((prev) => [...prev, doc])
  }
  
  const handleStartResearch = () => {
    if (!question.trim()) return
    setActiveQuestion(question)
    setIsResearching(true)
    setReport(null)
    setClaims([])
    setEvidence([])
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden">
      {/* Premium Background Effect */}
      <div className="fixed inset-0 z-0 h-full w-full bg-background bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]">
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-primary/20 opacity-30 blur-[100px]"></div>
      </div>

      <header className="border-b border-white/5 bg-background/60 backdrop-blur-md sticky top-0 z-50">
        <div className="container flex h-16 max-w-screen-2xl items-center px-8">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="flex"
          >
            <span className="font-extrabold sm:inline-block tracking-tighter text-2xl bg-clip-text text-transparent bg-gradient-to-r from-white to-white/50">
              RESEARCH<span className="text-primary">OS</span>
            </span>
          </motion.div>
        </div>
      </header>
      
      <main className="flex-1 flex flex-col items-center justify-start p-8 pt-16 z-10 relative">
        <div className="max-w-5xl w-full space-y-12">
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-center space-y-6"
          >
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-white via-white/90 to-white/30 drop-shadow-sm pb-2">
              Evidence-First Research
            </h1>
            <p className="text-muted-foreground text-xl max-w-2xl mx-auto font-medium">
              Decompose questions, retrieve exact evidence, and verify claims with 100% traceabilty.
            </p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="relative max-w-3xl mx-auto group"
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/30 to-primary/10 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative">
              <input 
                type="text" 
                placeholder="What do you want to deeply research?" 
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleStartResearch()}
                disabled={isResearching}
                className="flex h-16 w-full rounded-xl border border-white/10 bg-background/80 px-6 py-2 text-lg shadow-2xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 disabled:cursor-not-allowed disabled:opacity-50 pr-36 backdrop-blur-xl"
              />
              <button 
                onClick={handleStartResearch}
                disabled={isResearching}
                className="absolute right-2 top-2 h-12 px-8 bg-primary text-primary-foreground rounded-lg text-sm font-bold shadow-lg hover:shadow-primary/25 hover:bg-primary/90 transition-all disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
              >
                {isResearching ? 'Thinking...' : 'Deep Research'}
              </button>
            </div>
          </motion.div>

          <AnimatePresence mode="wait">
            {isResearching && (
              <motion.div 
                key="progress"
                initial={{ opacity: 0, height: 0, y: -20 }}
                animate={{ opacity: 1, height: 'auto', y: 0 }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-3xl mx-auto overflow-hidden"
              >
                <div className="pt-4">
                  <ResearchProgress 
                    question={activeQuestion} 
                    onComplete={(data) => {
                      setReport(data.report)
                      setClaims(data.claims || [])
                      setEvidence(data.evidence || [])
                      setIsResearching(false)
                    }} 
                  />
                </div>
              </motion.div>
            )}

            {report && (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, ease: "easeOut" }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                <div className="lg:col-span-2 space-y-8">
                  <div className="bg-card/40 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl prose prose-invert max-w-none relative">
                    <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent rounded-2xl pointer-events-none"></div>
                    <div className="flex justify-between items-start mb-6 border-b border-white/10 pb-4 relative z-10">
                      <h2 className="text-2xl font-bold m-0 bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">Research Report</h2>
                      <button 
                        onClick={() => {
                          const blob = new Blob([report], { type: 'text/markdown' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `research_report_${new Date().getTime()}.md`
                          a.click()
                        }}
                        className="px-4 py-2 text-xs font-semibold bg-white/5 border border-white/10 text-foreground rounded-lg hover:bg-white/10 transition-colors shadow-sm"
                      >
                        Export Markdown
                      </button>
                    </div>
                    <div className="whitespace-pre-wrap relative z-10 text-white/80 leading-relaxed">{report}</div>
                  </div>

                  <div className="space-y-4">
                    <h2 className="text-xl font-bold tracking-tight px-2">Evidence Graph</h2>
                    <div className="shadow-2xl rounded-2xl overflow-hidden border border-white/10 relative">
                      <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent pointer-events-none z-10 h-12 bottom-0"></div>
                      <EvidenceGraph 
                        question={activeQuestion}
                        claims={claims}
                        evidence={evidence}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-6">
                  <h3 className="text-xl font-bold tracking-tight px-2">Verified Claims</h3>
                  <div className="space-y-4">
                    {claims.length === 0 ? (
                      <div className="bg-card/40 backdrop-blur-md border border-white/5 rounded-2xl p-8 text-center text-muted-foreground shadow-lg">
                        No claims extracted.
                      </div>
                    ) : (
                      claims.map((claim, idx) => (
                        <motion.div 
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          key={idx} 
                          className="bg-card/40 backdrop-blur-sm border border-white/10 rounded-2xl p-5 shadow-lg space-y-4 hover:bg-card/60 transition-colors group relative overflow-hidden"
                        >
                          <div className="absolute top-0 left-0 w-1 h-full bg-primary/50 group-hover:bg-primary transition-colors"></div>
                          <p className="text-sm font-medium leading-relaxed">{claim.claim}</p>
                          <div className="flex flex-col space-y-3 pt-3 border-t border-white/10">
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <div className="flex space-x-2">
                                <span className="flex items-center space-x-1 text-emerald-400/90 font-medium bg-emerald-400/10 px-2 py-1 rounded-md">
                                  <span>{claim.supporting_source_ids?.length || 0}</span> <span>Support</span>
                                </span>
                                <span className="flex items-center space-x-1 text-rose-400/90 font-medium bg-rose-400/10 px-2 py-1 rounded-md">
                                  <span>{claim.contradicting_source_ids?.length || 0}</span> <span>Conflict</span>
                                </span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider ${
                                  claim.confidence_level === 'high' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                                  claim.confidence_level === 'medium' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                                  'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                }`}>
                                  {claim.confidence_level || 'low'}
                                </span>
                                <span className="font-mono bg-white/5 border border-white/10 px-2.5 py-1 rounded-md font-medium text-white/80">
                                  {claim.confidence}%
                                </span>
                              </div>
                            </div>
                            {claim.reasons && claim.reasons.length > 0 && (
                              <ul className="text-xs text-white/50 space-y-1 list-disc list-inside bg-black/20 p-2.5 rounded-lg border border-white/5">
                                {claim.reasons.map((r: string, i: number) => (
                                  <li key={i}>{r}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </motion.div>
                      ))
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {!isResearching && !report && (
              <motion.div 
                key="kb"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="grid grid-cols-1 gap-6 pt-12 mt-12 border-t border-white/5"
              >
                <div className="max-w-2xl mx-auto w-full">
                  <h2 className="text-xl font-bold mb-6 tracking-tight text-center bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">Knowledge Base</h2>
                  <div className="bg-card/20 backdrop-blur-md rounded-2xl p-1 border border-white/5 shadow-xl">
                    <FileUpload onUploadSuccess={handleUploadSuccess} />
                  </div>
                </div>

                {documents.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-3 mt-6 max-w-2xl mx-auto w-full"
                  >
                    <h3 className="text-sm font-semibold text-muted-foreground px-2">Recently Added Documents</h3>
                    <div className="space-y-2">
                      {documents.map((doc, i) => (
                        <div key={i} className="flex items-center justify-between p-4 border border-white/5 rounded-xl bg-card/30 backdrop-blur-sm hover:bg-card/50 transition-colors">
                          <span className="font-medium text-sm text-white/90">{doc.filename}</span>
                          <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-medium shadow-[0_0_10px_rgba(52,211,153,0.1)]">Indexed</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}

export default App
