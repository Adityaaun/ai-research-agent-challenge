import { useCallback, useState } from 'react'
import { UploadCloud, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface FileUploadProps {
  onUploadSuccess: (doc: any) => void
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [currentFile, setCurrentFile] = useState<File | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFiles = async (files: FileList) => {
    if (files.length === 0) return
    const file = files[0] // just handle one for now
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
      
      // Reset after 3 seconds
      setTimeout(() => {
        setUploadState('idle')
        setCurrentFile(null)
      }, 3000)
    } catch (err: any) {
      setUploadState('error')
      setErrorMsg(err.message || 'An error occurred during upload.')
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files)
    }
  }

  return (
    <div 
      className={cn(
        "relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all duration-200 bg-card/30 backdrop-blur-sm",
        isDragging ? "border-primary bg-primary/10" : "border-border hover:border-primary/50 hover:bg-card/50",
        uploadState === 'uploading' && "opacity-80 pointer-events-none"
      )}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <input 
        type="file" 
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
        onChange={onChange}
        accept=".txt,.pdf,.md,.csv"
        disabled={uploadState === 'uploading'}
      />
      
      {uploadState === 'idle' && (
        <>
          <UploadCloud className="w-10 h-10 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground">Drag & drop your documents</h3>
          <p className="text-sm text-muted-foreground mt-2">Support for PDF, TXT, MD, and CSV.</p>
        </>
      )}

      {uploadState === 'uploading' && (
        <div className="flex flex-col items-center">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <h3 className="text-lg font-medium text-foreground">Ingesting {currentFile?.name}...</h3>
          <p className="text-sm text-muted-foreground mt-2">Chunking and embedding vectors.</p>
        </div>
      )}

      {uploadState === 'success' && (
        <div className="flex flex-col items-center">
          <CheckCircle2 className="w-10 h-10 text-green-500 mb-4" />
          <h3 className="text-lg font-medium text-foreground">Document Indexed!</h3>
          <p className="text-sm text-muted-foreground mt-2">{currentFile?.name} is ready for research.</p>
        </div>
      )}

      {uploadState === 'error' && (
        <div className="flex flex-col items-center">
          <AlertCircle className="w-10 h-10 text-destructive mb-4" />
          <h3 className="text-lg font-medium text-destructive">Upload Failed</h3>
          <p className="text-sm text-muted-foreground mt-2">{errorMsg}</p>
        </div>
      )}
    </div>
  )
}
