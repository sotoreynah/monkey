import { useState, useEffect } from 'react'
import api from '../services/api'
import { formatCurrency, formatDate } from '../utils/formatters'

const PHASE_COLORS = {
  1: 'border-red-500 bg-red-50',
  2: 'border-orange-500 bg-orange-50',
  3: 'border-blue-500 bg-blue-50',
  4: 'border-green-500 bg-green-50',
}

export default function Reports() {
  const [milestones, setMilestones] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/reports/milestones')
      .then(res => setMilestones(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const toggleAchieved = async (id, current) => {
    await api.patch(`/reports/milestones/${id}`, null, {
      params: { is_achieved: !current },
    })
    setMilestones(prev =>
      prev.map(m => m.id === id ? { ...m, is_achieved: !current } : m)
    )
  }

  if (loading) return <div className="text-center py-12">Loading...</div>

  const grouped = {}
  milestones.forEach(m => {
    const phase = m.phase_number || 0
    if (!grouped[phase]) grouped[phase] = []
    grouped[phase].push(m)
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Reports & Milestones</h1>
      <p className="text-gray-500 mb-8">Track your Baby Steps and key milestones across all 4 phases</p>

      {Object.entries(grouped).map(([phase, items]) => (
        <div key={phase} className="mb-8">
          <h2 className="text-lg font-semibold mb-3">
            Phase {phase}
          </h2>
          <div className="space-y-3">
            {items.map(m => (
              <div
                key={m.id}
                className={`border-l-4 rounded-lg p-4 bg-white shadow-sm ${PHASE_COLORS[m.phase_number] || 'border-gray-300 bg-gray-50'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleAchieved(m.id, m.is_achieved)}
                      className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center text-xs transition-colors ${
                        m.is_achieved
                          ? 'bg-green-500 border-green-500 text-white'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {m.is_achieved ? '✓' : ''}
                    </button>
                    <div>
                      <p className={`font-medium ${m.is_achieved ? 'line-through text-gray-400' : ''}`}>
                        {m.name}
                      </p>
                      {m.description && (
                        <p className="text-sm text-gray-500 mt-0.5">{m.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right text-sm shrink-0 ml-4">
                    {m.target_date && (
                      <p className="text-gray-500">Target: {formatDate(m.target_date)}</p>
                    )}
                    {m.target_amount != null && (
                      <p className="text-gray-500">{formatCurrency(m.target_amount)}</p>
                    )}
                    {m.actual_date && (
                      <p className="text-green-600 font-medium">Achieved: {formatDate(m.actual_date)}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
