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

export default function Loans() {
  const [loans, setLoans] = useState([])
  const [summary, setSummary] = useState(null)
  const [projections, setProjections] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/loans'),
      api.get('/loans/summary'),
      api.get('/loans/projections'),
    ]).then(([l, s, p]) => {
      setLoans(l.data)
      setSummary(s.data)
      setProjections(p.data)
    })
    .catch(console.error)
    .finally(() => setLoading(false))
  }, [])

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
      <h1 className="text-2xl font-bold mb-6">Loan Tracker</h1>

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

      {/* Debt avalanche chart */}
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

      {/* Loan cards */}
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
                <span
                  className="text-xs px-2 py-0.5 rounded-full text-white"
                  style={{ backgroundColor: LOAN_COLORS[loan.loan_type] || '#6B7280' }}
                >
                  {loan.loan_type.replace('_', ' ')}
                </span>
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
    </div>
  )
}
