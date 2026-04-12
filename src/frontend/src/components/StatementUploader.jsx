import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'

import { useAuth } from '../context/AuthContext'
import { useForecast } from '../context/ForecastContext'
import { transactionAPI } from '../utils/api'

const ACCEPTED_EXTENSIONS = ['.csv', '.pdf']

const hasValidExtension = (name) => {
  if (!name) return false
  const lower = name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

export default function StatementUploader({ onSuccess }) {
  const { isAuthenticated } = useAuth()
  const { setEphemeralTransactions, clearEphemeralTransactions } = useForecast()
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')
  const [detectedHeaders, setDetectedHeaders] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  const validateAndSetFile = (candidate) => {
    if (!candidate) return
    if (!hasValidExtension(candidate.name)) {
      toast.error('Only .csv and .pdf files are supported')
      return
    }
    setFile(candidate)
    setStatus('idle')
    setMessage('')
    setDetectedHeaders(null)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    validateAndSetFile(dropped)
  }

  const handleFileChange = (e) => {
    const picked = e.target.files?.[0]
    validateAndSetFile(picked)
  }

  const handleClick = () => {
    if (status === 'uploading') return
    inputRef.current?.click()
  }

  const reset = (e) => {
    e?.stopPropagation()
    setFile(null)
    setStatus('idle')
    setMessage('')
    setDetectedHeaders(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleUpload = async (e) => {
    e?.stopPropagation()
    if (!file) return
    setStatus('uploading')
    setMessage('')
    setDetectedHeaders(null)
    try {
      let msg = ''

      if (isAuthenticated) {
        const response = await transactionAPI.uploadStatement(file)
        const imported = response.data.imported
        clearEphemeralTransactions()
        msg = `Imported ${imported} transactions`
      } else {
        const response = await transactionAPI.parseOnly(file)
        const parsed = Array.isArray(response.data)
          ? response.data
          : (response.data?.transactions || [])
        setEphemeralTransactions(parsed)
        msg = `Parsed ${parsed.length} transactions (demo mode)`
      }

      setStatus('success')
      setMessage(msg)
      toast.success(msg)
      setTimeout(() => {
        if (onSuccess) onSuccess()
      }, 1500)
    } catch (error) {
      const detail = error.response?.data?.detail
      setStatus('error')
      if (detail && typeof detail === 'object' && detail.detected_headers) {
        setDetectedHeaders(detail.detected_headers)
        setMessage(detail.message || 'Could not parse the statement')
      } else {
        setDetectedHeaders(null)
        setMessage(typeof detail === 'string' ? detail : 'Upload failed')
      }
      toast.error('Upload failed')
    }
  }

  const mutedStyle = { color: 'rgba(240, 244, 247, 0.6)' }
  const successStyle = { color: 'var(--radar-accent)' }
  const errorStyle = { color: '#ff6b6b' }

  const containerClass = [
    'glass-card p-8 text-center border-2 border-dashed rounded-2xl cursor-pointer',
    isDragging ? 'ring-2 ring-teal-400' : '',
  ].join(' ')

  return (
    <div
      className={containerClass}
      onClick={handleClick}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.pdf"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {(status === 'idle' || status === 'error') && !file && (
        <div>
          <div className="text-4xl mb-3">⬆️</div>
          <div className="font-medium mb-1">
            Drag and drop your bank statement here
          </div>
          <div className="text-sm" style={mutedStyle}>or click to browse</div>
          <div className="text-xs mt-2" style={mutedStyle}>Supports CSV and PDF</div>
        </div>
      )}

      {file && status === 'idle' && (
        <div className="soft-panel p-4 rounded-xl">
          <div className="font-medium">{file.name}</div>
          <div className="text-sm mb-4" style={mutedStyle}>
            {(file.size / 1024).toFixed(1)} KB
          </div>
          <button className="primary-cta" onClick={handleUpload}>
            Upload
          </button>
          <div
            className="text-xs mt-3 underline"
            style={mutedStyle}
            onClick={reset}
          >
            Click to change file
          </div>
        </div>
      )}

      {status === 'uploading' && (
        <div className="flex flex-col items-center gap-3">
          <div
            style={{
              width: 36,
              height: 36,
              border: '3px solid rgba(255,255,255,0.15)',
              borderTopColor: 'var(--radar-accent)',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }}
          />
          <div>Parsing your statement...</div>
          <button className="primary-cta" disabled style={{ opacity: 0.5 }}>
            Uploading
          </button>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {status === 'success' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="text-4xl mb-2">✅</div>
          <div style={successStyle}>{message}</div>
        </motion.div>
      )}

      {status === 'error' && (
        <div>
          <div className="text-4xl mb-2">⚠️</div>
          <div style={errorStyle}>{message}</div>
          {detectedHeaders && (
            <div className="text-sm mt-3" style={mutedStyle}>
              <div>We detected these columns: {detectedHeaders.join(', ')}</div>
              <div>Tip: rename them to Date, Amount, Description</div>
            </div>
          )}
          <button
            className="primary-cta mt-4"
            onClick={reset}
          >
            Try again
          </button>
        </div>
      )}
    </div>
  )
}
