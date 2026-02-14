import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../services/api'
import { formatCurrency, formatDate } from '../utils/formatters'

const LOAN_COLORS = {
  bnpl: '#F59E0B',
  credit_card: '#EF4444',
  auto: '#3B82F6',
  personal: '#8B5CF6',
  mortgage: '#6B7280',
}

const LOAN_TYPES = [
  { value: 'bnpl', label: 'BNPL' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'auto', label: 'Auto Loan' },
  { value: 'personal', label: 'Personal Loan' },
  { value: 'mortgage', label: 'Mortgage' },
]

const emptyForm = {
  name: '', loan_type: 'credit_card', creditor: '', original_amount: '',
  current_balance: '', interest_rate: '', monthly_payment: '',
  end_date: '', payments_remaining: '', priority_rank: '', notes: '', is_active: true,
}

function LoanModal({ loan, onClose, onSave }) {
  const isEdit = !!loan
  const [form, setForm] = useState(() => {
    if (loan) {
      return {
        name: loan.name || '',
        loan_type: loan.loan_type || 'credit_card',
        creditor: loan.creditor || '',
        original_amount: loan.original_amount || '',
        current_balance: loan.current_balance || '',
        interest_rate: loan.interest_rate ? (loan.interest_rate * 100).toFixed(2) : '',
        monthly_payment: loan.monthly_payment || '',
        end_date: loan.end_date || '',
        payments_remaining: loan.payments_remaining || '',
        priority_rank: loan.priority_rank || '',
        notes: loan.notes || '',
        is_active: loan.is_active !== false,
      }
    }
    return { ...emptyForm }
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)

    const payload = {
      name: form.name,
      loan_type: form.loan_type,
      creditor: form.creditor || null,
      original_amount: form.original_amount ? parseFloat(form.original_amount) : null,
      current_balance: parseFloat(form.current_balance),
      interest_rate: form.interest_rate ? parseFloat(form.interest_rate) / 100 : null,
      monthly_payment: form.monthly_payment ? parseFloat(form.monthly_payment) : null,
      end_date: form.end_date || null,
      payments_remaining: form.payments_remaining ? parseInt(form.payments_remaining) : null,
      priority_rank: form.priority_rank ? parseInt(form.priority_rank) : null,
      notes: form.notes || null,
    }
    if (isEdit) payload.is_active = form.is_active

    try {
      if (isEdit) {
        await api.patch(`/loans/${loan.id}`, payload)
      } else {
        await api.post('/loans', payload)
      }
      onSave()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save loan')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">{isEdit ? 'Edit Loan' : 'Add Loan'}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input type="text" name="name" value={form.name} onChange={handleChange} required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
                <select name="loan_type" value={form.loan_type} onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                  {LOAN_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Creditor</label>
                <input type="text" name="creditor" value={form.creditor} onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Original Amount</label>
                <input type="number" name="original_amount" value={form.original_amount} onChange={handleChange}
                  step="0.01" min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Balance *</label>
                <input type="number" name="current_balance" value={form.current_balance} onChange={handleChange}
                  required step="0.01" min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Interest Rate %</label>
                <input type="number" name="interest_rate" value={form.interest_rate} onChange={handleChange}
                  step="0.01" min="0" max="100" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Payment</label>
                <input type="number" name="monthly_payment" value={form.monthly_payment} onChange={handleChange}
                  step="0.01" min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input type="date" name="end_date" value={form.end_date} onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payments Remaining</label>
                <input type="number" name="payments_remaining" value={form.payments_remaining} onChange={handleChange}
                  min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority Rank</label>
                <input type="number" name="priority_rank" value={form.priority_rank} onChange={handleChange}
                  min="1" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea name="notes" value={form.notes} onChange={handleChange} rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            {isEdit && (
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" name="is_active" checked={form.is_active} onChange={handleChange} />
                Active
              </label>
            )}

            {error && <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg text-sm">{error}</div>}

            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={saving}
                className="flex-1 bg-gray-900 text-white py-2 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm">
                {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Loan'}
              </button>
              <button type="button" onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function Loans() {
  const [loans, setLoans] = useState([])
  const [summary, setSummary] = useState(null)
  const [projections, setProjections] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalLoan, setModalLoan] = useState(undefined) // undefined=closed, null=add, loan=edit

  const fetchAll = () => {
    return Promise.all([
      api.get('/loans'),
      api.get('/loans/summary'),
      api.get('/loans/projections'),
    ]).then(([l, s, p]) => {
      setLoans(l.data)
      setSummary(s.data)
      setProjections(p.data)
    }).catch(console.error)
  }

  useEffect(() => {
    fetchAll().finally(() => setLoading(false))
  }, [])

  const handleDelete = async (loan) => {
    if (!window.confirm(`Delete "${loan.name}"? This cannot be undone.`)) return
    try {
      await api.delete(`/loans/${loan.id}`)
      await fetchAll()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete loan')
    }
  }

  const handleModalSave = async () => {
    setModalLoan(undefined)
    await fetchAll()
  }

  if (loading) return <div className="text-center py-12">Loading loans...</div>

  const chartData = loans
    .filter(l => l.loan_type !== 'mortgage')
    .sort((a, b) => (a.priority_rank || 99) - (b.priority_rank || 99))
    .map(l => ({
      name: l.name.length > 15 ? l.name.slice(0, 15) + '...' : l.name,
      balance: l.current_balance,
      type: l.loan_type,
    }))

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Loan Tracker</h1>
        <button
          onClick={() => setModalLoan(null)}
          className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          + Add Loan
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow p-5">
            <p className="text-sm text-gray-500">Total Debt</p>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(summary.total_debt)}</p>
          </div>
          <div className="bg-white rounded-xl shadow p-5">
            <p className="text-sm text-gray-500">Non-Mortgage</p>
            <p className="text-2xl font-bold text-orange-600">{formatCurrency(summary.non_mortgage_debt)}</p>
          </div>
          <div className="bg-white rounded-xl shadow p-5">
            <p className="text-sm text-gray-500">Mortgage</p>
            <p className="text-2xl font-bold text-gray-600">{formatCurrency(summary.mortgage_debt)}</p>
          </div>
          <div className="bg-white rounded-xl shadow p-5">
            <p className="text-sm text-gray-500">Monthly Payments</p>
            <p className="text-2xl font-bold">{formatCurrency(summary.monthly_payments)}</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {loans.length === 0 && (
        <div className="bg-gray-50 rounded-xl p-12 text-center mb-8">
          <div className="text-4xl mb-3">🏦</div>
          <p className="text-gray-500 mb-4">No loans added yet. Add your first loan to start tracking.</p>
          <button
            onClick={() => setModalLoan(null)}
            className="bg-gray-900 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            + Add Your First Loan
          </button>
        </div>
      )}

      {/* Debt avalanche chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Debt Avalanche Order (Non-Mortgage)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
              <Tooltip formatter={v => formatCurrency(v)} />
              <Bar dataKey="balance" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={LOAN_COLORS[entry.type] || '#6B7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-4 mt-4 justify-center">
            {Object.entries(LOAN_COLORS).filter(([k]) => k !== 'mortgage').map(([type, color]) => (
              <span key={type} className="flex items-center gap-1 text-xs">
                <span className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                {type.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Loan cards */}
      {loans.length > 0 && (
        <>
          <h2 className="text-lg font-semibold mb-4">All Active Loans</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {loans.map(loan => {
              const proj = projections.find(p => p.loan_id === loan.id)
              return (
                <div key={loan.id} className="bg-white rounded-xl shadow p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold">{loan.name}</h3>
                      <p className="text-xs text-gray-400">{loan.creditor}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs px-2 py-0.5 rounded-full text-white"
                        style={{ backgroundColor: LOAN_COLORS[loan.loan_type] || '#6B7280' }}
                      >
                        {loan.loan_type.replace('_', ' ')}
                      </span>
                      <button
                        onClick={() => setModalLoan(loan)}
                        className="text-gray-400 hover:text-gray-700 text-sm"
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(loan)}
                        className="text-gray-400 hover:text-red-600 text-sm"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Balance</p>
                      <p className="font-bold text-lg">{formatCurrency(loan.current_balance)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Monthly Payment</p>
                      <p className="font-bold">{formatCurrency(loan.monthly_payment || 0)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Interest Rate</p>
                      <p className="font-bold">{loan.interest_rate ? (loan.interest_rate * 100).toFixed(1) + '%' : 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Payoff Date</p>
                      <p className="font-bold">
                        {loan.end_date ? formatDate(loan.end_date)
                          : proj?.projected_payoff_date ? formatDate(proj.projected_payoff_date)
                          : 'TBD'}
                      </p>
                    </div>
                  </div>
                  {loan.priority_rank && loan.priority_rank < 99 && (
                    <div className="mt-3 pt-3 border-t text-xs text-gray-400">
                      Payoff priority: #{loan.priority_rank}
                      {proj && <span className="ml-3">Total interest remaining: {formatCurrency(proj.total_interest_remaining)}</span>}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Modal */}
      {modalLoan !== undefined && (
        <LoanModal
          loan={modalLoan}
          onClose={() => setModalLoan(undefined)}
          onSave={handleModalSave}
        />
      )}
    </div>
  )
}
