import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '../services/api'
import { formatCurrency, formatDate } from '../utils/formatters'

export default function DebtPayoff() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [payoffPlan, setPayoffPlan] = useState(null)
  const [monthlyCapacity, setMonthlyCapacity] = useState(8000)
  const [recalculating, setRecalculating] = useState(false)

  useEffect(() => {
    loadPayoffPlan()
  }, [])

  const loadPayoffPlan = async () => {
    try {
      setLoading(true)
      setError(null)
      const { data } = await api.get('/debt/payoff-plan')
      setPayoffPlan(data)
      setMonthlyCapacity(data.summary.monthly_capacity)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load debt payoff plan')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const recalculate = async () => {
    try {
      setRecalculating(true)
      setError(null)
      const { data } = await api.post('/debt/recalculate', {
        monthly_capacity: parseFloat(monthlyCapacity)
      })
      setPayoffPlan(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to recalculate')
      console.error(err)
    } finally {
      setRecalculating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl text-gray-600">Loading debt payoff calculator...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-semibold">Error</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadPayoffPlan}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!payoffPlan) return null

  const { summary, payoff_order, timeline } = payoffPlan

  // Prepare timeline chart data (show every 6 months for readability)
  const chartData = timeline.filter((_, i) => i % 6 === 0 || i === timeline.length - 1).map(t => ({
    month: `M${t.month}`,
    debt: t.total_debt_remaining,
    interest: t.interest_portion,
    principal: t.principal_portion,
  }))

  // Calculate extra payment available
  const extraPayment = summary.monthly_capacity - summary.total_minimum_payments

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">💰 Debt Payoff Calculator</h1>
        <div className="text-sm text-gray-500">
          Using Debt Avalanche Method (Highest Interest First)
        </div>
      </div>

      {/* Warning Banner */}
      {summary.warning && (
        <div className={`border-l-4 p-4 rounded-md ${
          summary.debt_paid_off 
            ? 'bg-yellow-50 border-yellow-500' 
            : 'bg-red-50 border-red-500'
        }`}>
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <span className="text-2xl">{summary.debt_paid_off ? '⚠️' : '🚨'}</span>
            </div>
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${
                summary.debt_paid_off ? 'text-yellow-800' : 'text-red-800'
              }`}>
                {summary.debt_paid_off ? 'Below Minimum Payments' : 'Critical: Debt Growing'}
              </h3>
              <div className={`mt-2 text-sm ${
                summary.debt_paid_off ? 'text-yellow-700' : 'text-red-700'
              }`}>
                <p>{summary.warning}</p>
                <p className="mt-2">
                  <strong>Minimum payments needed:</strong> {formatCurrency(summary.total_minimum_payments)}
                  {' • '}
                  <strong>Your capacity:</strong> {formatCurrency(summary.monthly_capacity)}
                  {' • '}
                  <strong>Shortfall:</strong> {formatCurrency(summary.total_minimum_payments - summary.monthly_capacity)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner for Extra Payment */}
      {!summary.warning && extraPayment > 0 && (
        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-md">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <span className="text-2xl">✅</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">On Track!</h3>
              <p className="text-sm text-green-700">
                You're paying {formatCurrency(extraPayment)} above minimums each month.
                This extra payment is accelerating your debt payoff using the debt avalanche method.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`bg-gradient-to-br border rounded-lg p-6 ${
          summary.debt_free_date 
            ? 'from-green-50 to-green-100 border-green-200' 
            : 'from-gray-50 to-gray-100 border-gray-300'
        }`}>
          <div className={`text-sm font-medium mb-1 ${summary.debt_free_date ? 'text-green-600' : 'text-gray-600'}`}>
            Debt-Free Date
          </div>
          <div className={`text-2xl font-bold ${summary.debt_free_date ? 'text-green-900' : 'text-gray-500'}`}>
            {summary.debt_free_date ? formatDate(summary.debt_free_date) : 'Never'}
          </div>
          <div className={`text-xs mt-1 ${summary.debt_free_date ? 'text-green-600' : 'text-gray-500'}`}>
            {summary.months_to_debt_free ? `${summary.months_to_debt_free} months` : 'Increase payments'}
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
          <div className="text-blue-600 text-sm font-medium mb-1">Total Debt</div>
          <div className="text-2xl font-bold text-blue-900">{formatCurrency(summary.total_debt)}</div>
          <div className="text-blue-600 text-xs mt-1">Principal amount</div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-6">
          <div className="text-purple-600 text-sm font-medium mb-1">Total Interest</div>
          <div className="text-2xl font-bold text-purple-900">{formatCurrency(summary.total_interest_paid)}</div>
          <div className="text-purple-600 text-xs mt-1">Over {summary.months_to_debt_free} months</div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200 rounded-lg p-6">
          <div className="text-orange-600 text-sm font-medium mb-1">Monthly Capacity</div>
          <div className="text-2xl font-bold text-orange-900">{formatCurrency(summary.monthly_capacity)}</div>
          <div className="text-orange-600 text-xs mt-1">Total payment budget</div>
        </div>
      </div>

      {/* What-If Calculator */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">💡 What-If Calculator</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Payment Capacity
            </label>
            <input
              type="number"
              value={monthlyCapacity}
              onChange={(e) => setMonthlyCapacity(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              step="100"
            />
          </div>
          <button
            onClick={recalculate}
            disabled={recalculating || parseFloat(monthlyCapacity) === summary.monthly_capacity}
            className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {recalculating ? 'Recalculating...' : 'Recalculate'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Try different payment amounts to see how it affects your debt-free date
        </p>
      </div>

      {/* Timeline Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">📈 Debt Payoff Timeline</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Line
              type="monotone"
              dataKey="debt"
              stroke="#3B82F6"
              strokeWidth={2}
              name="Remaining Debt"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Monthly Payment Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">💸 Payment Breakdown</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(value) => formatCurrency(value)} />
            <Legend />
            <Bar dataKey="principal" stackId="a" fill="#10B981" name="Principal" />
            <Bar dataKey="interest" stackId="a" fill="#EF4444" name="Interest" />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-500 mt-2 text-center">
          Over time, more of your payment goes to principal (green) vs interest (red)
        </p>
      </div>

      {/* Payoff Order Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">🎯 Payoff Order (Debt Avalanche)</h2>
          <p className="text-sm text-gray-500 mt-1">
            Paying off highest interest rate loans first
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Loan Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payoff Month
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payoff Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interest Paid
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payoff_order.map((loan) => (
                <tr key={loan.loan_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-semibold text-sm">
                      {loan.rank}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                    {loan.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    Month {loan.payoff_month}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {formatDate(loan.payoff_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {formatCurrency(loan.interest_paid)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">📊 Plan Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-blue-600">Total Paid:</span>{' '}
            <span className="font-semibold text-blue-900">{formatCurrency(summary.total_paid)}</span>
          </div>
          <div>
            <span className="text-blue-600">Principal:</span>{' '}
            <span className="font-semibold text-blue-900">{formatCurrency(summary.total_debt)}</span>
          </div>
          <div>
            <span className="text-blue-600">Interest:</span>{' '}
            <span className="font-semibold text-blue-900">{formatCurrency(summary.total_interest_paid)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
