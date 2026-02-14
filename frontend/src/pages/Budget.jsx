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
  const [editMode, setEditMode] = useState(false)
  const [editedTargets, setEditedTargets] = useState({})

  useEffect(() => {
    setLoading(true)
    setEditMode(false)
    api.get('/budget', { params: { month } })
      .then(res => {
        setData(res.data)
        // Initialize edited targets from current data
        const targets = {}
        res.data.categories.forEach(c => {
          targets[c.category] = c.target
        })
        setEditedTargets(targets)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [month])

  const handleTargetChange = (category, value) => {
    setEditedTargets(prev => ({
      ...prev,
      [category]: parseFloat(value) || 0
    }))
  }

  const handleSave = async () => {
    const targetsArray = Object.entries(editedTargets).map(([category, monthly_target]) => ({
      category,
      monthly_target,
      is_fixed: false
    }))

    try {
      await api.post(`/budget/targets/${month}`, targetsArray)
      setEditMode(false)
      // Reload data
      const res = await api.get('/budget', { params: { month } })
      setData(res.data)
    } catch (err) {
      console.error('Failed to save budget targets:', err)
      alert('Failed to save budget targets')
    }
  }

  const handleCopyFromPrevious = async () => {
    const [year, monthNum] = month.split('-').map(Number)
    const prevDate = new Date(year, monthNum - 2, 1) // -2 because monthNum is 1-indexed
    const prevMonth = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`

    if (confirm(`Copy budget targets from ${prevMonth}?`)) {
      try {
        await api.post(`/budget/targets/${month}/copy-from/${prevMonth}`)
        // Reload data
        const res = await api.get('/budget', { params: { month } })
        setData(res.data)
        const targets = {}
        res.data.categories.forEach(c => {
          targets[c.category] = c.target
        })
        setEditedTargets(targets)
      } catch (err) {
        console.error('Failed to copy budget targets:', err)
        alert('Failed to copy budget targets from previous month')
      }
    }
  }

  const handleAddCategory = () => {
    const category = prompt('Enter category name:')
    if (category && category.trim()) {
      setEditedTargets(prev => ({
        ...prev,
        [category.trim()]: 0
      }))
    }
  }

  if (loading) return <div className="text-center py-12">Loading budget...</div>
  if (!data) return <div className="text-center py-12">No budget data</div>

  const chartData = data.categories
    .filter(c => c.target > 0 || c.actual > 0)
    .sort((a, b) => b.actual - a.actual)
  
  // Calculate totals using edited targets if in edit mode
  const totalTarget = editMode 
    ? Object.values(editedTargets).reduce((sum, val) => sum + val, 0)
    : data.total_target
  const totalVariance = totalTarget - data.total_actual

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
          {!editMode ? (
            <>
              <button
                onClick={() => setEditMode(true)}
                className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
              >
                Edit Budget
              </button>
              <button
                onClick={handleCopyFromPrevious}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Copy from Previous
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
              >
                Save Changes
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCategory}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                + Add Category
              </button>
            </>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Budget Target {editMode && <span className="text-xs">(editing)</span>}</p>
          <p className="text-2xl font-bold">{formatCurrency(totalTarget)}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Actual Spent</p>
          <p className="text-2xl font-bold">{formatCurrency(data.total_actual)}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-gray-500">Variance</p>
          <p className={`text-2xl font-bold ${totalVariance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalVariance >= 0 ? '+' : ''}{formatCurrency(totalVariance)}
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
            {data.categories.map(row => {
              const editedTarget = editedTargets[row.category] ?? row.target
              const variance = editedTarget - row.actual
              const overBudget = row.actual > editedTarget && editedTarget > 0
              
              return (
                <tr key={row.category} className="border-t">
                  <td className="px-4 py-2 font-medium">{row.category}</td>
                  <td className="px-4 py-2 text-right text-gray-500">
                    {editMode ? (
                      <input
                        type="number"
                        value={editedTarget}
                        onChange={e => handleTargetChange(row.category, e.target.value)}
                        className="w-28 px-2 py-1 border rounded text-right"
                        step="0.01"
                      />
                    ) : (
                      formatCurrency(row.target)
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">{formatCurrency(row.actual)}</td>
                  <td className={`px-4 py-2 text-right ${variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {variance >= 0 ? '+' : ''}{formatCurrency(variance)}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {overBudget
                      ? <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Over</span>
                      : <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">OK</span>
                    }
                  </td>
                </tr>
              )
            })}
            {editMode && Object.keys(editedTargets).filter(cat => !data.categories.find(c => c.category === cat)).map(category => (
              <tr key={category} className="border-t bg-blue-50">
                <td className="px-4 py-2 font-medium">{category}</td>
                <td className="px-4 py-2 text-right">
                  <input
                    type="number"
                    value={editedTargets[category]}
                    onChange={e => handleTargetChange(category, e.target.value)}
                    className="w-28 px-2 py-1 border rounded text-right"
                    step="0.01"
                  />
                </td>
                <td className="px-4 py-2 text-right text-gray-400">$0.00</td>
                <td className="px-4 py-2 text-right text-gray-400">—</td>
                <td className="px-4 py-2 text-center">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">New</span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td className="px-4 py-3">Total</td>
              <td className="px-4 py-3 text-right">{formatCurrency(totalTarget)}</td>
              <td className="px-4 py-3 text-right">{formatCurrency(data.total_actual)}</td>
              <td className={`px-4 py-3 text-right ${totalVariance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalVariance >= 0 ? '+' : ''}{formatCurrency(totalVariance)}
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
