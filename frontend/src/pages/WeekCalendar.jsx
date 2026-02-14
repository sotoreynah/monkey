import { useState, useEffect } from 'react'
import api from '../services/api'
import { formatCurrency, formatShortDate } from '../utils/formatters'

const PHASE_META = {
  1: { color: 'bg-red-500', hoverColor: 'hover:bg-red-400', name: 'Phase 1: Stop the Bleeding' },
  2: { color: 'bg-orange-500', hoverColor: 'hover:bg-orange-400', name: 'Phase 2: Debt Avalanche' },
  3: { color: 'bg-blue-500', hoverColor: 'hover:bg-blue-400', name: 'Phase 3: Build Fortress' },
  4: { color: 'bg-green-500', hoverColor: 'hover:bg-green-400', name: 'Phase 4: Build Runway' },
}

export default function WeekCalendar() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    api.get('/plan/calendar')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-12">Loading calendar...</div>
  if (!data) return <div className="text-center py-12">No plan data found</div>

  const { weeks, phases, current_week, progress_pct } = data
  const WEEKS_PER_ROW = 52

  // Build rows
  const rows = []
  for (let i = 0; i < weeks.length; i += WEEKS_PER_ROW) {
    rows.push(weeks.slice(i, i + WEEKS_PER_ROW))
  }

  return (
    <div>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Your 252-Week Journey</h1>
        <p className="text-gray-500">
          Week {current_week} of 252 &middot; {Math.round(progress_pct)}% complete
        </p>
      </div>

      {/* Phase legend */}
      <div className="flex flex-wrap justify-center gap-4 mb-6">
        {phases.map(p => (
          <div key={p.phase_number} className="flex items-center gap-2">
            <span className={`w-4 h-4 rounded-sm ${PHASE_META[p.phase_number].color}`} />
            <span className="text-sm text-gray-700">{p.name}</span>
            <span className="text-xs text-gray-400">({p.weeks_completed}/{p.weeks_total})</span>
          </div>
        ))}
      </div>

      {/* Status legend */}
      <div className="flex justify-center gap-6 mb-8 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-gray-900" /> Completed</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-yellow-400 current-week-pulse" /> Current</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-gray-300" /> Future</span>
      </div>

      {/* Week grid */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8 overflow-x-auto">
        {/* Month labels */}
        <div className="flex gap-[3px] mb-1 ml-8">
          {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map(m => (
            <div key={m} className="text-[9px] text-gray-400 font-medium" style={{ width: `${(52/12)*15}px`, minWidth: '40px' }}>{m}</div>
          ))}
        </div>

        {rows.map((row, rowIdx) => (
          <div key={rowIdx} className="flex items-center gap-[3px] mb-[3px]">
            <div className="w-8 text-[10px] text-gray-400 text-right pr-1 shrink-0">
              {2026 + rowIdx}
            </div>
            {row.map(week => {
              const isCurrent = week.week_number === current_week
              const meta = PHASE_META[week.phase_number]
              const isCompleted = week.status === 'completed'
              const isFuture = week.status === 'future'

              let className = `w-[13px] h-[13px] rounded-[2px] week-box relative `
              if (isCurrent) {
                className += `${meta.color} ring-2 ring-yellow-400 ring-offset-1 current-week-pulse `
              } else if (isCompleted) {
                className += `${meta.color} `
                if (week.is_on_track === false) {
                  className += 'ring-1 ring-yellow-600 '
                }
              } else if (isFuture) {
                className += `${meta.color} opacity-25 `
              } else {
                className += `${meta.color} opacity-50 `
              }

              return (
                <div
                  key={week.week_number}
                  className={className}
                  onMouseEnter={() => setHovered(week)}
                  onMouseLeave={() => setHovered(null)}
                  title={`Week ${week.week_number}`}
                />
              )
            })}
          </div>
        ))}
      </div>

      {/* Hovered week detail */}
      {hovered && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border-l-4" style={{ borderColor: PHASE_META[hovered.phase_number]?.color === 'bg-red-500' ? '#EF4444' : PHASE_META[hovered.phase_number]?.color === 'bg-orange-500' ? '#F97316' : PHASE_META[hovered.phase_number]?.color === 'bg-blue-500' ? '#3B82F6' : '#10B981' }}>
          <h3 className="font-semibold text-lg mb-3">
            Week {hovered.week_number} &middot; {formatShortDate(hovered.week_start_date)} - {formatShortDate(hovered.week_end_date)}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Total Spent</p>
              <p className="text-xl font-bold">{formatCurrency(hovered.total_spent)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Debt Paid Down</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(hovered.debt_paid_down)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Emergency Fund</p>
              <p className="text-xl font-bold">{formatCurrency(hovered.emergency_fund_balance)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className={`text-xl font-semibold ${hovered.is_on_track === true ? 'text-green-600' : hovered.is_on_track === false ? 'text-red-600' : 'text-gray-400'}`}>
                {hovered.is_on_track === true ? 'On Track' : hovered.is_on_track === false ? 'Over Budget' : hovered.status === 'future' ? 'Future' : 'Pending'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Phase progress cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {phases.map(p => (
          <div key={p.phase_number} className="bg-white rounded-xl shadow p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className={`w-3 h-3 rounded-full ${PHASE_META[p.phase_number].color}`} />
              <h4 className="font-semibold text-sm">{p.name}</h4>
            </div>
            <p className="text-xs text-gray-500 mb-3">{p.primary_goal}</p>
            <div className="bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${PHASE_META[p.phase_number].color}`}
                style={{ width: `${p.progress_pct}%` }}
              />
            </div>
            <p className="text-xs text-gray-400">
              {p.weeks_completed} of {p.weeks_total} weeks ({Math.round(p.progress_pct)}%)
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
