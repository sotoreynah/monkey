import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import api from '../services/api'
import { formatCurrency } from '../utils/formatters'

export default function Budget() {
  const [data, setData] = useState(null)
  const [month, setMonth] = useState(() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get('/budget', { params: { month } })
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [month])

  if (loading) return <div className="text-center py-12">Loading budget...</div>
  if (!data) return <div className="text-center py-12">No budget data</div>

  const chartData = data.categories
    .filter(c => c.target > 0 || c.actual > 0)
    .sort((a, b) => b.actual - a.actual)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Budget vs Actual</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">Phase {data.phase}</span>
          <input
            type="month"
            value={month}
            onChange={e => setMonth(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          />
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Budget Target</p>
          <p className="text-2xl font-bold">{formatCurrency(data.total_target)}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Actual Spent</p>
          <p className="text-2xl font-bold">{formatCurrency(data.total_actual)}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Variance</p>
          <p className={`text-2xl font-bold ${data.total_variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {data.total_variance >= 0 ? '+' : ''}{formatCurrency(data.total_variance)}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">By Category</h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" tickFormatter={v => `$${v.toLocaleString()}`} />
            <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => formatCurrency(v)} />
            <Legend />
            <Bar dataKey="target" fill="#D1D5DB" name="Budget" radius={[0, 4, 4, 0]} />
            <Bar dataKey="actual" fill="#111827" name="Actual" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detail table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Category</th>
              <th className="text-right px-4 py-3 font-medium">Target</th>
              <th className="text-right px-4 py-3 font-medium">Actual</th>
              <th className="text-right px-4 py-3 font-medium">Variance</th>
              <th className="text-center px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.categories.map(row => (
              <tr key={row.category} className="border-t">
                <td className="px-4 py-2 font-medium">{row.category}</td>
                <td className="px-4 py-2 text-right text-gray-500">{formatCurrency(row.target)}</td>
                <td className="px-4 py-2 text-right">{formatCurrency(row.actual)}</td>
                <td className={`px-4 py-2 text-right ${row.variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {row.variance >= 0 ? '+' : ''}{formatCurrency(row.variance)}
                </td>
                <td className="px-4 py-2 text-center">
                  {row.over_budget
                    ? <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Over</span>
                    : <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">OK</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td className="px-4 py-3">Total</td>
              <td className="px-4 py-3 text-right">{formatCurrency(data.total_target)}</td>
              <td className="px-4 py-3 text-right">{formatCurrency(data.total_actual)}</td>
              <td className={`px-4 py-3 text-right ${data.total_variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.total_variance >= 0 ? '+' : ''}{formatCurrency(data.total_variance)}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
