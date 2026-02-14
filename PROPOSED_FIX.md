# Proposed Fix: Exclude Payments from Spending Calculations

## Issue
Credit card payments are being counted as "spending" which inflates the monthly spending trend by ~$16k/month on average.

## Root Cause
The dashboard query counts ALL debit transactions (`is_debit = True`), which includes:
- Actual spending (groceries, dining, etc.)
- Credit card payments (paying off existing debt)

## Impact
- September 2025: Shows $72k, should show $53k (27% inflation)
- Annual: ~$191k in payments incorrectly counted as spending

## Solution
Add `category != 'Payment'` filter to spending queries in `dashboard.py`

---

## Code Changes

### File: `backend/app/api/dashboard.py`

**Line 39-44 (Current - WRONG):**
```python
month_spent = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= month_start,
    Transaction.is_debit == True,
    Transaction.is_excluded == False,
).scalar() or 0
```

**Line 39-45 (Fixed - CORRECT):**
```python
month_spent = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= month_start,
    Transaction.is_debit == True,
    Transaction.is_excluded == False,
    Transaction.category != 'Payment',  # ← NEW LINE
).scalar() or 0
```

---

**Line 51-57 (Current - WRONG):**
```python
spent = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= m_start,
    Transaction.transaction_date <= m_end,
    Transaction.is_debit == True,
    Transaction.is_excluded == False,
).scalar() or 0
```

**Line 51-58 (Fixed - CORRECT):**
```python
spent = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= m_start,
    Transaction.transaction_date <= m_end,
    Transaction.is_debit == True,
    Transaction.is_excluded == False,
    Transaction.category != 'Payment',  # ← NEW LINE
).scalar() or 0
```

---

## Expected Results After Fix

### Monthly Spending Trend
| Month | Before | After | Correction |
|-------|--------|-------|-----------|
| Sep 2025 | $72,702 | $53,122 | -$19,580 |
| Oct 2025 | $64,130 | ~$40,000 | -$24,000 (est) |
| Nov 2025 | $36,280 | ~$32,000 | -$4,500 (est) |
| Dec 2025 | $40,295 | ~$26,000 | -$14,500 (est) |
| Jan 2026 | $34,240 | ~$20,000 | -$14,000 (est) |
| Feb 2026 | $21,306 | ~$8,000 | -$13,500 (est) |

These are **much more realistic** spending numbers!

---

## Additional Improvements (Optional)

### 1. Also check transaction descriptions
Some payments might not have category='Payment' but are clearly payments:

```python
# More robust payment detection
is_payment = (
    (Transaction.category == 'Payment') |
    (Transaction.description.contains('PAYMENT')) |
    (Transaction.description.contains('PMT')) |
    (Transaction.description.contains('AUTOPAY'))
)

month_spent = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= month_start,
    Transaction.is_debit == True,
    Transaction.is_excluded == False,
    ~is_payment,  # Exclude payments
).scalar() or 0
```

### 2. Add a new metric for debt payments
Track payments separately as "Debt Paid This Month":

```python
debt_paid_this_month = db.query(func.sum(Transaction.amount)).filter(
    Transaction.transaction_date >= month_start,
    Transaction.is_debit == True,
    Transaction.category == 'Payment',
).scalar() or 0
```

---

## Testing
After applying fix, check:
1. Dashboard spending numbers drop significantly ✅
2. Chart shows more realistic trend ✅
3. Budget variance makes more sense ✅

---

## Ready to Apply?
Would you like me to:
1. ✅ Apply this fix directly to dashboard.py
2. 📊 Recalculate and show new chart values
3. 🔄 Restart the backend container
