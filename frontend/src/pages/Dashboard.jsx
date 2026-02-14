import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import api from '../services/api'
import { formatCurrency } from '../utils/formatters'

function MetricCard({ label, value, sub, color = 'text-gray-900', bg = 'bg-white' }) {
  return (
    <div className={`${bg} rounded-xl shadow p-5`}>
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

const PHASE_COLORS = { 1: 'bg-red-500', 2: 'bg-orange-500', 3: 'bg-blue-500', 4: 'bg-green-500' }
const PHASE_NAMES = { 1: 'Stop the Bleeding', 2: 'Debt Avalanche', 3: 'Build Fortress', 4: 'Build Runway' }

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/dashboard')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-12">Loading dashboard...</div>
  if (!data) return <div className="text-center py-12">Failed to load dashboard</div>

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-500">
            Week {data.current_week} of 252 &middot; {Math.round(data.progress_pct)}% complete
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-block w-3 h-3 rounded-full ${PHASE_COLORS[data.current_phase]}`} />
          <span className="text-sm font-medium">{data.current_phase_name}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="bg-gray-200 rounded-full h-3 mb-8">
        <div
          className="bg-gray-900 h-3 rounded-full transition-all"
          style={{ width: `${data.progress_pct}%` }}
        />
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Total Debt"
          value={formatCurrency(data.total_debt)}
          sub="All loans including mortgage"
          color="text-red-600"
        />
        <MetricCard
          label="Non-Mortgage Debt"
          value={formatCurrency(data.non_mortgage_debt)}
          sub="Target: $0"
          color="text-orange-600"
        />
        <MetricCard
          label="Spent This Month"
          value={formatCurrency(data.month_spent)}
          sub={`Target: ${formatCurrency(data.month_budget_target)}`}
          color={data.month_variance >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <MetricCard
          label="Emergency Fund"
          value={formatCurrency(data.emergency_fund)}
          sub="Target: $156,000"
        />
      </div>

      {/* Spending trend chart */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Monthly Spending Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.spending_trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={v => formatCurrency(v)} />
            <ReferenceLine y={data.month_budget_target} stroke="#10B981" strokeDasharray="5 5" label="Target" />
            <Line type="monotone" dataKey="spent" stroke="#111827" strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/calendar" className="bg-white rounded-xl shadow p-5 text-center hover:shadow-md transition-shadow">
          <div className="text-3xl mb-2">📅</div>
          <p className="font-medium">Week Calendar</p>
        </Link>
        <Link to="/import" className="bg-white rounded-xl shadow p-5 text-center hover:shadow-md transition-shadow">
          <div className="text-3xl mb-2">📤</div>
          <p className="font-medium">Upload CSV</p>
        </Link>
        <Link to="/loans" className="bg-white rounded-xl shadow p-5 text-center hover:shadow-md transition-shadow">
          <div className="text-3xl mb-2">🏦</div>
          <p className="font-medium">Loan Tracker</p>
        </Link>
        <Link to="/budget" className="bg-white rounded-xl shadow p-5 text-center hover:shadow-md transition-shadow">
          <div className="text-3xl mb-2">📋</div>
          <p className="font-medium">Budget</p>
        </Link>
      </div>
    </div>
  )
}
