import { useState, useEffect } from 'react'
import api from '../services/api'
import { formatCurrency } from '../utils/formatters'

export default function EmergencyFundWidget() {
  const [loading, setLoading] = useState(true)
  const [fund, setFund] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState('deposit') // 'deposit' or 'withdraw'
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadFund()
  }, [])

  const loadFund = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/emergency-fund')
      setFund(data)
    } catch (err) {
      console.error('Failed to load emergency fund:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTransaction = async (e) => {
    e.preventDefault()
    if (!amount || parseFloat(amount) <= 0) return

    try {
      setSubmitting(true)
      await api.post(`/emergency-fund/${modalType}`, {
        amount: parseFloat(amount),
        description: description || null
      })
      setShowModal(false)
      setAmount('')
      setDescription('')
      loadFund()
    } catch (err) {
      alert(err.response?.data?.detail || 'Transaction failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">Loading emergency fund...</div>
      </div>
    )
  }

  if (!fund) return null

  const progressColor = fund.progress_percent < 25 ? 'bg-red-500' :
                        fund.progress_percent < 75 ? 'bg-yellow-500' :
                        'bg-green-500'

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">💰 Emergency Fund</h3>
          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
            Baby Step {fund.baby_step}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">
              {formatCurrency(fund.current_balance)} / {formatCurrency(fund.target)}
            </span>
            <span className="font-semibold text-gray-900">{fund.progress_percent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`${progressColor} h-3 rounded-full transition-all duration-500`}
              style={{ width: `${Math.min(fund.progress_percent, 100)}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <div className="text-gray-500">Months of Expenses</div>
            <div className="font-semibold text-gray-900">
              {fund.months_of_expenses.toFixed(1)} months
            </div>
          </div>
          <div>
            <div className="text-gray-500">Next Milestone</div>
            <div className="font-semibold text-gray-900">
              {fund.next_milestone.name.replace('Baby Step 1: ', '').replace('Baby Step 3: ', '')}
            </div>
          </div>
        </div>

        {/* Milestone Message */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4 text-sm">
          {fund.baby_step === 1 ? (
            <div>
              <strong>Goal:</strong> Save ${fund.target.toLocaleString()} starter emergency fund
              <br />
              <strong>Remaining:</strong> {formatCurrency(fund.target - fund.current_balance)}
            </div>
          ) : (
            <div>
              <strong>Goal:</strong> Build 12 months of expenses ({formatCurrency(fund.target)})
              <br />
              <strong>Progress:</strong> {fund.months_of_expenses.toFixed(1)} of 12 months saved
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => { setModalType('deposit'); setShowModal(true) }}
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
          >
            Add Deposit
          </button>
          <button
            onClick={() => { setModalType('withdraw'); setShowModal(true) }}
            className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm font-medium"
          >
            Record Withdrawal
          </button>
        </div>
      </div>

      {/* Transaction Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">
              {modalType === 'deposit' ? '💵 Add Deposit' : '💸 Record Withdrawal'}
            </h3>
            <form onSubmit={handleTransaction}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0.00"
                  required
                  autoFocus
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optional)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Paycheck savings, Car repair, etc."
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setAmount(''); setDescription('') }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`flex-1 px-4 py-2 rounded-md text-white ${
                    modalType === 'deposit'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : modalType === 'deposit' ? 'Add Deposit' : 'Record Withdrawal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
