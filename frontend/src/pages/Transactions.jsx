import { useState, useEffect } from 'react'
import api from '../services/api'
import { formatCurrencyExact, formatDate } from '../utils/formatters'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [sources, setSources] = useState([])
  const [categories, setCategories] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    source_id: '', category: '', date_from: '', date_to: '', search: '',
  })

  useEffect(() => {
    Promise.all([
      api.get('/transactions/sources'),
      api.get('/transactions/categories'),
    ]).then(([s, c]) => {
      setSources(s.data)
      setCategories(c.data)
    })
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = { page, per_page: 50 }
    if (filters.source_id) params.source_id = filters.source_id
    if (filters.category) params.category = filters.category
    if (filters.date_from) params.date_from = filters.date_from
    if (filters.date_to) params.date_to = filters.date_to
    if (filters.search) params.search = filters.search

    api.get('/transactions', { params })
      .then(res => {
        setTransactions(res.data.transactions)
        setTotal(res.data.total)
        setPages(res.data.pages)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page, filters])

  const updateCategory = async (txnId, newCategory) => {
    await api.patch(`/transactions/${txnId}`, { category: newCategory })
    setTransactions(prev => prev.map(t =>
      t.id === txnId ? { ...t, category: newCategory } : t
    ))
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Transactions</h1>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow p-4 mb-6 grid grid-cols-2 md:grid-cols-5 gap-3">
        <input
          type="text"
          placeholder="Search..."
          value={filters.search}
          onChange={e => { setFilters(f => ({ ...f, search: e.target.value })); setPage(1) }}
          className="px-3 py-2 border rounded-lg text-sm"
        />
        <select
          value={filters.source_id}
          onChange={e => { setFilters(f => ({ ...f, source_id: e.target.value })); setPage(1) }}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">All Sources</option>
          {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select
          value={filters.category}
          onChange={e => { setFilters(f => ({ ...f, category: e.target.value })); setPage(1) }}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <input
          type="date"
          value={filters.date_from}
          onChange={e => { setFilters(f => ({ ...f, date_from: e.target.value })); setPage(1) }}
          className="px-3 py-2 border rounded-lg text-sm"
        />
        <input
          type="date"
          value={filters.date_to}
          onChange={e => { setFilters(f => ({ ...f, date_to: e.target.value })); setPage(1) }}
          className="px-3 py-2 border rounded-lg text-sm"
        />
      </div>

      {/* Results */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 flex justify-between items-center">
          <span className="text-sm text-gray-500">{total.toLocaleString()} transactions</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 text-sm border rounded disabled:opacity-30"
            >Prev</button>
            <span className="text-sm py-1">Page {page} of {pages}</span>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="px-3 py-1 text-sm border rounded disabled:opacity-30"
            >Next</button>
          </div>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Date</th>
              <th className="text-left px-4 py-2 font-medium">Source</th>
              <th className="text-left px-4 py-2 font-medium">Description</th>
              <th className="text-left px-4 py-2 font-medium">Category</th>
              <th className="text-right px-4 py-2 font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : transactions.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">No transactions found</td></tr>
            ) : transactions.map(t => (
              <tr key={t.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 whitespace-nowrap">{formatDate(t.transaction_date)}</td>
                <td className="px-4 py-2 whitespace-nowrap">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100">{t.source_name}</span>
                </td>
                <td className="px-4 py-2 max-w-xs truncate">{t.description}</td>
                <td className="px-4 py-2">
                  <select
                    value={t.category || ''}
                    onChange={e => updateCategory(t.id, e.target.value)}
                    className="text-xs px-2 py-1 border rounded bg-transparent"
                  >
                    <option value="">Uncategorized</option>
                    {categories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </td>
                <td className={`px-4 py-2 text-right font-mono whitespace-nowrap ${t.is_debit ? 'text-red-600' : 'text-green-600'}`}>
                  {t.is_debit ? '-' : '+'}{formatCurrencyExact(t.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
