import { useCallback, useState } from 'react'
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, Link as LinkIcon, FileText } from 'lucide-react'
import { cn } from '../../lib/utils'

interface FileUploadProps {
  onUploadSuccess: (doc: any) => void
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [mode, setMode] = useState<'file' | 'url'>('file')
  const [url, setUrl] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [currentFile, setCurrentFile] = useState<File | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (mode === 'file') setIsDragging(true)
  }, [mode])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFiles = async (files: FileList) => {
    if (files.length === 0) return
    const file = files[0]
    setCurrentFile(file)
    setUploadState('uploading')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      setUploadState('success')
      onUploadSuccess(data)
      
      setTimeout(() => {
        setUploadState('idle')
        setCurrentFile(null)
      }, 3000)
    } catch (err: any) {
      setUploadState('error')
      setErrorMsg(err.message || 'An error occurred during upload.')
    }
  }

  const handleUrl = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    setUploadState('uploading')
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/documents/ingest-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url.trim() }),
      })

      if (!response.ok) {
        throw new Error('URL ingestion failed')
      }

      const data = await response.json()
      setUploadState('success')
      onUploadSuccess(data)
      
      setTimeout(() => {
        setUploadState('idle')
        setUrl('')
      }, 3000)
    } catch (err: any) {
      setUploadState('error')
      setErrorMsg(err.message || 'An error occurred during URL ingestion.')
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (mode === 'file' && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files)
    }
  }

  return (
    <div className="w-full">
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setMode('file'); setUploadState('idle') }}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors",
            mode === 'file' ? "bg-primary text-primary-foreground" : "bg-card/50 text-muted-foreground hover:bg-card"
          )}
        >
          <FileText className="w-4 h-4" />
          File Upload
        </button>
        <button
          onClick={() => { setMode('url'); setUploadState('idle') }}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors",
            mode === 'url' ? "bg-primary text-primary-foreground" : "bg-card/50 text-muted-foreground hover:bg-card"
          )}
        >
          <LinkIcon className="w-4 h-4" />
          Web URL
        </button>
      </div>

      <div 
        className={cn(
          "relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all duration-200 bg-card/30 backdrop-blur-sm min-h-[200px]",
          isDragging ? "border-primary bg-primary/10" : "border-border hover:border-primary/50 hover:bg-card/50",
          uploadState === 'uploading' && "opacity-80 pointer-events-none"
        )}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        {mode === 'file' && uploadState === 'idle' && (
          <>
            <input 
              type="file" 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
              onChange={onChange}
              accept=".txt,.pdf,.md,.csv"
            />
            <UploadCloud className="w-10 h-10 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground">Drag & drop your documents</h3>
            <p className="text-sm text-muted-foreground mt-2">Support for PDF, TXT, MD, and CSV.</p>
          </>
        )}

        {mode === 'url' && uploadState === 'idle' && (
          <form onSubmit={handleUrl} className="w-full max-w-md flex flex-col items-center z-10">
            <LinkIcon className="w-10 h-10 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-4">Ingest Web Article</h3>
            <div className="flex w-full gap-2">
              <input
                type="url"
                required
                placeholder="https://en.wikipedia.org/wiki/..."
                className="flex-1 bg-background/50 border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={url}
                onChange={e => setUrl(e.target.value)}
              />
              <button 
                type="submit"
                className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Fetch
              </button>
            </div>
          </form>
        )}

        {uploadState === 'uploading' && (
          <div className="flex flex-col items-center z-10">
            <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
            <h3 className="text-lg font-medium text-foreground">
              {mode === 'file' ? `Ingesting ${currentFile?.name}...` : 'Fetching & Scraping URL...'}
            </h3>
            <p className="text-sm text-muted-foreground mt-2">Chunking and embedding vectors.</p>
          </div>
        )}

        {uploadState === 'success' && (
          <div className="flex flex-col items-center z-10">
            <CheckCircle2 className="w-10 h-10 text-green-500 mb-4" />
            <h3 className="text-lg font-medium text-foreground">Successfully Indexed!</h3>
            <p className="text-sm text-muted-foreground mt-2">
              {mode === 'file' ? currentFile?.name : 'URL'} is ready for research.
            </p>
          </div>
        )}

        {uploadState === 'error' && (
          <div className="flex flex-col items-center z-10 relative z-20">
            <AlertCircle className="w-10 h-10 text-destructive mb-4" />
            <h3 className="text-lg font-medium text-destructive">Ingestion Failed</h3>
            <p className="text-sm text-muted-foreground mt-2 text-center max-w-md break-words">{errorMsg}</p>
            <button 
              onClick={() => setUploadState('idle')}
              className="mt-4 px-4 py-2 bg-destructive/10 text-destructive rounded-lg text-sm font-medium hover:bg-destructive/20"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
