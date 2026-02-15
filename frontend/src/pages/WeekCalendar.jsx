import { useState, useEffect } from 'react'
import api from '../services/api'

const PHASE_COLORS = {
  1: '#ff6b6b',
  2: '#ffa726',
  3: '#42a5f5',
  4: '#66bb6a',
}

const PHASE_NAMES = {
  1: 'Stop The Bleeding',
  2: 'Debt Avalanche',
  3: 'Build Fortress',
  4: 'Build Runway',
}

export default function WeekCalendar() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/plan/calendar')
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl text-gray-600">Loading your 252-week journey...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No plan data found</p>
      </div>
    )
  }

  const { weeks, current_week, progress_pct } = data

  return (
    <div style={{ padding: '50px' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <h1 style={{
          fontSize: '36px',
          marginBottom: '13px',
          fontWeight: '700',
          fontFamily: 'Comic Sans MS, Comic Neue, cursive'
        }}>
          🐵 Stop The Monkey - 252 Week Journey
        </h1>
        
        <p style={{
          fontSize: '18px',
          color: '#666',
          marginBottom: '50px',
          fontFamily: 'Comic Sans MS, Comic Neue, cursive'
        }}>
          Your path to financial freedom, one week at a time
        </p>

        {/* Progress Text */}
        <p style={{
          fontSize: '20px',
          marginBottom: '38px',
          color: '#333',
          fontFamily: 'Comic Sans MS, Comic Neue, cursive'
        }}>
          <strong>Week {current_week} of 252</strong> • {Math.round(progress_pct * 10) / 10}% complete • {252 - current_week} weeks to go
        </p>

        {/* Legend */}
        <div style={{
          display: 'flex',
          gap: '30px',
          marginBottom: '38px',
          fontSize: '14px',
          flexWrap: 'wrap',
          fontFamily: 'Comic Sans MS, Comic Neue, cursive'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #333',
              backgroundColor: PHASE_COLORS[1]
            }} />
            <span>Phase 1: Stop The Bleeding (Weeks 1-26)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #333',
              backgroundColor: PHASE_COLORS[2]
            }} />
            <span>Phase 2: Debt Avalanche (27-58)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #333',
              backgroundColor: PHASE_COLORS[3]
            }} />
            <span>Phase 3: Build Fortress (59-194)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              border: '2px solid #333',
              backgroundColor: PHASE_COLORS[4]
            }} />
            <span>Phase 4: Build Runway (195-252)</span>
          </div>
        </div>

        {/* Week Grid */}
        <div style={{
          background: 'white',
          padding: '38px',
          borderRadius: '10px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(52, 1fr)',
            gap: '4px'
          }}>
            {weeks.map((week) => {
              const isCompleted = week.week_number < current_week
              const isCurrent = week.week_number === current_week
              const phaseColor = PHASE_COLORS[week.phase_number]
              const phaseName = PHASE_NAMES[week.phase_number]

              return (
                <div
                  key={week.week_number}
                  title={`Week ${week.week_number} - ${phaseName}`}
                  style={{
                    aspectRatio: '1',
                    border: isCurrent ? '3px solid #000' : '2px solid #333',
                    backgroundColor: phaseColor,
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    backgroundImage: isCompleted
                      ? 'repeating-linear-gradient(45deg, transparent, transparent 2px, #333 2px, #333 4px)'
                      : 'none',
                    animation: isCurrent ? 'pulse 1s infinite' : 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.2)'
                    e.currentTarget.style.zIndex = '10'
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)'
                    e.currentTarget.style.zIndex = '1'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                />
              )
            })}
          </div>
        </div>
      </div>

      {/* Pulse animation for current week */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  )
}
