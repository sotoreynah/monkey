import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { formatDate, formatCurrency } from '../utils/formatters'

const LOAN_TYPES = [
  { value: 'bnpl', label: 'BNPL' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'auto', label: 'Auto Loan' },
  { value: 'personal', label: 'Personal Loan' },
  { value: 'mortgage', label: 'Mortgage' },
]

const emptyLoan = {
  name: '', loan_type: 'credit_card', creditor: '', current_balance: '',
  interest_rate: '', monthly_payment: '', end_date: '', payments_remaining: '', priority_rank: '',
}

export default function Import() {
  const [history, setHistory] = useState([])
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loans, setLoans] = useState([])
  const [loanForm, setLoanForm] = useState({ ...emptyLoan })
  const [loanSuccess, setLoanSuccess] = useState(null)
  const [loanError, setLoanError] = useState(null)
  const [showLoanForm, setShowLoanForm] = useState(false)

  useEffect(() => {
    api.get('/imports/history').then(res => setHistory(res.data)).catch(console.error)
    api.get('/loans').then(res => setLoans(res.data)).catch(console.error)
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

  const handleLoanChange = (e) => {
    setLoanForm({ ...loanForm, [e.target.name]: e.target.value })
  }

  const handleLoanSubmit = async (e) => {
    e.preventDefault()
    setLoanSuccess(null)
    setLoanError(null)

    const payload = {
      name: loanForm.name,
      loan_type: loanForm.loan_type,
      creditor: loanForm.creditor || null,
      current_balance: parseFloat(loanForm.current_balance),
      interest_rate: loanForm.interest_rate ? parseFloat(loanForm.interest_rate) / 100 : null,
      monthly_payment: loanForm.monthly_payment ? parseFloat(loanForm.monthly_payment) : null,
      end_date: loanForm.end_date || null,
      payments_remaining: loanForm.payments_remaining ? parseInt(loanForm.payments_remaining) : null,
      priority_rank: loanForm.priority_rank ? parseInt(loanForm.priority_rank) : null,
    }

    try {
      await api.post('/loans', payload)
      setLoanSuccess(`Added "${payload.name}" successfully`)
      setLoanForm({ ...emptyLoan })
      const res = await api.get('/loans')
      setLoans(res.data)
    } catch (err) {
      setLoanError(err.response?.data?.detail || 'Failed to add loan')
    }
  }

  const isEmpty = history.length === 0 && loans.length === 0

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Import Data</h1>

      {/* Getting started banner */}
      {isEmpty && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-blue-800 mb-2">Welcome! Let's get started</h3>
          <p className="text-sm text-blue-700">
            Upload your transaction CSVs below and add your loans to initialize the app.
            Supported formats: Credit Card 6032, Apple Card, AMEX, Checking 1569.
          </p>
        </div>
      )}

      {/* CSV Upload zone */}
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

      {/* Upload result */}
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

      {/* Upload error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
          <h3 className="font-semibold text-red-800 mb-1">Import Failed</h3>
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Add Loan section */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Add a Loan</h2>
          <button
            onClick={() => setShowLoanForm(!showLoanForm)}
            className="text-sm px-3 py-1 rounded-lg border border-gray-300 hover:bg-gray-50"
          >
            {showLoanForm ? 'Hide Form' : '+ Add Loan'}
          </button>
        </div>

        {showLoanForm && (
          <form onSubmit={handleLoanSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text" name="name" value={loanForm.name} onChange={handleLoanChange}
                  required placeholder="e.g. Dyson, Auto Loan, Mortgage"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select
                  name="loan_type" value={loanForm.loan_type} onChange={handleLoanChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                >
                  {LOAN_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Creditor</label>
                <input
                  type="text" name="creditor" value={loanForm.creditor} onChange={handleLoanChange}
                  placeholder="e.g. Affirm, US Bank"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Balance *</label>
                <input
                  type="number" name="current_balance" value={loanForm.current_balance} onChange={handleLoanChange}
                  required step="0.01" min="0" placeholder="5000.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Interest Rate %</label>
                <input
                  type="number" name="interest_rate" value={loanForm.interest_rate} onChange={handleLoanChange}
                  step="0.01" min="0" max="100" placeholder="6.99"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Payment</label>
                <input
                  type="number" name="monthly_payment" value={loanForm.monthly_payment} onChange={handleLoanChange}
                  step="0.01" min="0" placeholder="500.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date" name="end_date" value={loanForm.end_date} onChange={handleLoanChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payments Remaining</label>
                <input
                  type="number" name="payments_remaining" value={loanForm.payments_remaining} onChange={handleLoanChange}
                  min="0" placeholder="12"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority Rank</label>
                <input
                  type="number" name="priority_rank" value={loanForm.priority_rank} onChange={handleLoanChange}
                  min="1" placeholder="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                />
              </div>
              <div className="md:col-span-2 flex items-end">
                <button
                  type="submit"
                  className="w-full bg-gray-900 text-white py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors text-sm"
                >
                  Add Loan
                </button>
              </div>
            </div>

            {loanSuccess && (
              <div className="bg-green-50 text-green-700 px-4 py-2 rounded-lg text-sm">{loanSuccess}</div>
            )}
            {loanError && (
              <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm">{loanError}</div>
            )}
          </form>
        )}

        {/* Loans summary */}
        {loans.length > 0 && (
          <div className={showLoanForm ? 'mt-4 pt-4 border-t' : ''}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-500">{loans.length} loan{loans.length !== 1 ? 's' : ''} added</p>
              <Link to="/loans" className="text-sm text-blue-600 hover:underline">View all loans →</Link>
            </div>
            <div className="flex flex-wrap gap-2">
              {loans.map(l => (
                <span key={l.id} className="inline-flex items-center gap-1 bg-gray-100 px-3 py-1 rounded-full text-xs">
                  {l.name} <span className="text-gray-400">({formatCurrency(l.current_balance)})</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Import History */}
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
