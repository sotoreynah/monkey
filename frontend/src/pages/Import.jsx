import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import api from '../services/api'
import { formatDate } from '../utils/formatters'

export default function Import() {
  const [history, setHistory] = useState([])
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/imports/history').then(res => setHistory(res.data)).catch(console.error)
  }, [])

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    setResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/imports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
      // Refresh history
      const h = await api.get('/imports/history')
      setHistory(h.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Import Data</h1>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`bg-white rounded-xl shadow-lg border-2 border-dashed p-12 text-center cursor-pointer transition-colors mb-8 ${
          isDragActive ? 'border-gray-900 bg-gray-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-4">{uploading ? '...' : '📤'}</div>
        {uploading ? (
          <p className="text-gray-500">Uploading and processing...</p>
        ) : isDragActive ? (
          <p className="text-gray-900 font-medium">Drop the CSV file here</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium mb-1">Drag and drop a CSV file here, or click to browse</p>
            <p className="text-sm text-gray-400">Supported: Credit Card 6032, Apple Card, AMEX, Checking 1569</p>
            <p className="text-xs text-gray-400 mt-1">Auto-detects format from column headers</p>
          </>
        )}
      </div>

      {/* Result */}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-green-800 mb-2">Import Successful</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-green-600">Source</p>
              <p className="font-medium">{result.source_name}</p>
            </div>
            <div>
              <p className="text-green-600">Imported</p>
              <p className="font-medium">{result.rows_imported} rows</p>
            </div>
            <div>
              <p className="text-green-600">Duplicates Skipped</p>
              <p className="font-medium">{result.rows_skipped} rows</p>
            </div>
            <div>
              <p className="text-green-600">Date Range</p>
              <p className="font-medium">
                {result.date_range_start && formatDate(result.date_range_start)} - {result.date_range_end && formatDate(result.date_range_end)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-red-800 mb-1">Import Failed</h3>
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* History */}
      <h2 className="text-lg font-semibold mb-4">Import History</h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Date</th>
              <th className="text-left px-4 py-3 font-medium">File</th>
              <th className="text-left px-4 py-3 font-medium">Source</th>
              <th className="text-right px-4 py-3 font-medium">Imported</th>
              <th className="text-right px-4 py-3 font-medium">Skipped</th>
              <th className="text-left px-4 py-3 font-medium">Date Range</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No imports yet</td></tr>
            ) : history.map(h => (
              <tr key={h.batch_id} className="border-t">
                <td className="px-4 py-2 whitespace-nowrap">{h.imported_at ? new Date(h.imported_at).toLocaleString() : ''}</td>
                <td className="px-4 py-2 max-w-xs truncate">{h.filename}</td>
                <td className="px-4 py-2">{h.source_name}</td>
                <td className="px-4 py-2 text-right text-green-600 font-medium">{h.rows_imported}</td>
                <td className="px-4 py-2 text-right text-gray-400">{h.rows_skipped}</td>
                <td className="px-4 py-2 text-xs text-gray-500">
                  {h.date_range_start && formatDate(h.date_range_start)} - {h.date_range_end && formatDate(h.date_range_end)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
