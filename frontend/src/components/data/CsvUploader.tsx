import { FileSpreadsheet, UploadCloud } from 'lucide-react'
import { useCallback, useId, useRef, useState, type DragEvent } from 'react'
import { cx } from '../../lib/utils'

const MAX_SIZE_BYTES = 50 * 1024 * 1024

export interface CsvUploaderProps {
  onUpload: (file: File) => void
  isUploading?: boolean
  serverError?: string | null
}

export function CsvUploader({ onUpload, isUploading = false, serverError = null }: CsvUploaderProps) {
  const [isDragging, setDragging] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const inputId = useId()

  const validateAndUpload = useCallback(
    (file: File) => {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        setLocalError('Only .csv files are accepted.')
        return
      }
      if (file.size === 0) {
        setLocalError('That file is empty.')
        return
      }
      if (file.size > MAX_SIZE_BYTES) {
        setLocalError('File exceeds the 50 MB limit.')
        return
      }
      setLocalError(null)
      setFileName(file.name)
      onUpload(file)
    },
    [onUpload],
  )

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    if (isUploading) return
    const file = e.dataTransfer.files?.[0]
    if (file) validateAndUpload(file)
  }

  const error = localError ?? serverError

  return (
    <div className="flex flex-col gap-md">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!isUploading) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-disabled={isUploading}
        aria-describedby={error ? `${inputId}-error` : undefined}
        onClick={() => !isUploading && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isUploading) {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        className={cx(
          'flex min-h-[160px] flex-col items-center justify-center gap-md rounded-lg border-2 border-dashed px-xl py-2xl text-center transition-colors duration-200',
          isDragging ? 'border-primary bg-muted' : 'border-border-strong bg-surface',
          isUploading ? 'cursor-not-allowed opacity-70' : 'cursor-pointer hover:border-primary',
        )}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept=".csv"
          className="sr-only"
          disabled={isUploading}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) validateAndUpload(file)
            e.target.value = ''
          }}
        />
        {isUploading ? (
          <>
            <FileSpreadsheet className="h-10 w-10 text-primary" aria-hidden="true" />
            <p className="text-sm font-medium text-text-primary">Uploading {fileName}...</p>
            <div className="h-md w-48 overflow-hidden rounded-full bg-muted">
              <div className="h-full w-1/2 animate-pulse rounded-full bg-primary" />
            </div>
          </>
        ) : (
          <>
            <UploadCloud className="h-10 w-10 text-text-muted" aria-hidden="true" />
            <p className="text-sm font-medium text-text-primary">
              Drag and drop a CSV file here, or click to browse
            </p>
            <p className="text-caption text-text-muted">CSV only, up to 50 MB</p>
          </>
        )}
      </div>
      {error && (
        <p id={`${inputId}-error`} role="alert" className="text-sm text-critical">
          {error}
        </p>
      )}
    </div>
  )
}
