# Data Features Implementation Plan

**Focus:** Functionality over aesthetics  
**Goal:** Make Stop The Monkey actually useful for debt crushing  
**Timeline:** 2-3 weeks (5 features)

---

## 🎯 **Priority Order**

| Priority | Feature | Why First | Time |
|----------|---------|-----------|------|
| **1** | Debt Payoff Calculator | Answers #1 question: "When am I debt-free?" | 2 days |
| **2** | Emergency Fund Tracker | Baby Steps 1 & 3 - core to plan | 1 day |
| **3** | Monthly Snapshot Generator | Automates budget tracking | 2 days |
| **4** | Progress Dashboard | Shows plan progress at a glance | 1 day |
| **5** | Spending Trends | Month-over-month insights | 1 day |

**Total:** ~7 days of focused work

---

## 📊 **Feature 1: Debt Payoff Calculator**

### **What it does:**
- Calculates timeline to debt-free based on current debt + monthly payment capacity
- Shows debt avalanche order (highest interest → lowest)
- Projects interest paid vs saved
- Visualizes payoff timeline with milestones

### **Database Requirements:**

**Already have:**
- ✅ `loans` table (16 debts with balance, rate, monthly payment, priority)

**Need to add:**
```sql
-- Add payment_capacity to plan
ALTER TABLE financial_plan ADD COLUMN monthly_payment_capacity FLOAT DEFAULT 5413;

-- Add debt_payoff_projections table
CREATE TABLE debt_payoff_projections (
  id INTEGER PRIMARY KEY,
  plan_id INTEGER REFERENCES financial_plan(id),
  loan_id INTEGER REFERENCES loans(id),
  payoff_month INTEGER NOT NULL,
  payoff_date DATE NOT NULL,
  total_paid FLOAT NOT NULL,
  interest_paid FLOAT NOT NULL,
  principal_paid FLOAT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Backend API:**

**New endpoints:**
```python
# GET /api/debt/payoff-plan
# Returns complete debt avalanche timeline
{
  "summary": {
    "total_debt": 85000,
    "monthly_capacity": 5413,
    "months_to_debt_free": 18,
    "debt_free_date": "2027-08-01",
    "total_interest_paid": 4200,
    "interest_saved": 8300
  },
  "payoff_order": [
    {
      "rank": 1,
      "loan_id": 8,
      "name": "Credit Card 6032",
      "balance": 5000,
      "rate": 0.22,
      "minimum_payment": 150,
      "payoff_month": 3,
      "payoff_date": "2026-05-01",
      "total_interest": 320
    },
    ...
  ],
  "timeline": [
    {
      "month": "2026-02",
      "total_debt_remaining": 85000,
      "total_paid": 5413,
      "interest_portion": 1250,
      "principal_portion": 4163,
      "active_loan": "Credit Card 6032"
    },
    ...
  ]
}

# POST /api/debt/recalculate
# Recalculates projections when debt balances update
# Body: { "monthly_capacity": 5413 }
```

### **Algorithm:**

```python
def calculate_debt_payoff(loans, monthly_capacity):
    """
    Debt Avalanche Algorithm
    1. Sort by priority (interest rate high → low)
    2. Each month:
       - Pay minimums on all loans
       - Apply extra to highest priority loan
       - When loan paid off, move to next
    3. Track interest paid, principal, payoff dates
    """
    
    timeline = []
    loans = sorted(loans, key=lambda x: x.priority_rank)
    current_month = 0
    
    while any(loan.balance > 0 for loan in loans):
        current_month += 1
        monthly_interest = 0
        monthly_principal = 0
        
        # Calculate interest for all loans
        for loan in loans:
            if loan.balance > 0:
                interest = loan.balance * (loan.rate / 12)
                loan.balance += interest
                monthly_interest += interest
        
        # Pay minimums
        remaining_payment = monthly_capacity
        for loan in loans:
            if loan.balance > 0:
                minimum = loan.minimum_payment or (loan.balance * 0.02)
                payment = min(minimum, loan.balance, remaining_payment)
                loan.balance -= payment
                monthly_principal += payment
                remaining_payment -= payment
        
        # Apply extra to highest priority
        for loan in loans:
            if loan.balance > 0 and remaining_payment > 0:
                extra = min(remaining_payment, loan.balance)
                loan.balance -= extra
                monthly_principal += extra
                remaining_payment -= extra
                break
        
        timeline.append({
            "month": current_month,
            "debt_remaining": sum(l.balance for l in loans),
            "interest_paid": monthly_interest,
            "principal_paid": monthly_principal
        })
    
    return timeline
```

### **Frontend Component:**

**New page:** `/debt-payoff`

**Sections:**
1. **Summary Cards:**
   - Months to debt-free
   - Debt-free date
   - Total interest paid
   - Interest saved (vs minimum payments forever)

2. **Payoff Order Table:**
   - Rank, Loan Name, Balance, Rate, Payoff Month
   - Color-coded by priority (red = attacking now, gray = future)

3. **Timeline Chart:**
   - Line chart: Total debt over time (months)
   - Stacked area: Interest vs principal paid
   - Milestones: When each loan is paid off

4. **What-If Calculator:**
   - Slider: Adjust monthly payment capacity
   - See new timeline in real-time
   - "If I add $500/mo, I'm debt-free 4 months earlier"

### **Quick Win Implementation:**

**Day 1:**
- Create debt_payoff_projections table
- Implement algorithm in backend
- Create API endpoint
- Test with current 16 loans

**Day 2:**
- Build frontend page
- Summary cards + payoff order table
- Basic timeline chart (Recharts)
- Deploy & test

---

## 💰 **Feature 2: Emergency Fund Tracker**

### **What it does:**
- Tracks progress toward Baby Step 1 ($1,000)
- Tracks progress toward Baby Step 3 ($156,000 = 12 months expenses)
- Shows current balance, target, percentage complete
- Suggests monthly contribution needed to reach goal by Phase 3

### **Database Requirements:**

**Need to add:**
```sql
-- Add emergency_fund table
CREATE TABLE emergency_fund (
  id INTEGER PRIMARY KEY,
  current_balance FLOAT NOT NULL DEFAULT 0,
  target_step_1 FLOAT NOT NULL DEFAULT 1000,
  target_step_3 FLOAT NOT NULL DEFAULT 156000,
  monthly_contribution FLOAT DEFAULT 0,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with zero balance
INSERT INTO emergency_fund (current_balance) VALUES (0);

-- Add emergency fund transactions
CREATE TABLE emergency_fund_transactions (
  id INTEGER PRIMARY KEY,
  transaction_date DATE NOT NULL,
  amount FLOAT NOT NULL,
  type TEXT NOT NULL,  -- 'deposit' or 'withdrawal'
  description TEXT,
  balance_after FLOAT NOT NULL
);
```

### **Backend API:**

```python
# GET /api/emergency-fund
{
  "current_balance": 0,
  "baby_step": 1,  # 1 or 3
  "target": 1000,  # Current step target
  "progress_percent": 0,
  "months_of_expenses": 0,
  "monthly_contribution_needed": 200,  # To reach Step 3 by Phase 3 end
  "projected_completion_date": "2029-07-01",
  "next_milestone": {
    "name": "Baby Step 1",
    "amount": 1000,
    "percent": 0
  }
}

# POST /api/emergency-fund/deposit
# Body: { "amount": 500, "description": "Paycheck savings" }

# POST /api/emergency-fund/withdraw
# Body: { "amount": 200, "description": "Car repair emergency" }

# GET /api/emergency-fund/history
# Returns list of transactions
```

### **Frontend Component:**

**New section on Dashboard:** `<EmergencyFundWidget>`

**Display:**
1. **Progress Bar:**
   - Current balance / Target
   - Color: Red (0-25%), Yellow (25-75%), Green (75-100%)
   - Text: "$0 / $1,000 (0%)"

2. **Baby Steps Indicator:**
   - Step 1: $1,000 starter fund
   - Step 2: Pay off debt (link to debt payoff page)
   - Step 3: $156,000 full emergency fund (12 months)

3. **Quick Actions:**
   - "Add Deposit" button → modal
   - "Record Withdrawal" button → modal
   - Transaction history link

4. **Motivation:**
   - "You're X months of expenses away from sleeping easy"
   - "Complete Step 1 in X weeks at $Y/week"

### **Quick Win Implementation:**

**Day 1:**
- Create tables
- Build API endpoints
- Create EmergencyFundWidget component
- Add to Dashboard page
- Manual deposit/withdraw UI

**Progress tracking automatically updates based on balance.**

---

## 📸 **Feature 3: Monthly Snapshot Generator**

### **What it does:**
- Automatically calculates monthly budget performance
- Runs monthly (cron job or manual trigger)
- Populates `monthly_snapshots` table
- Shows budget adherence, debt paydown, spending trends

### **Database Requirements:**

**Already have:**
- ✅ `monthly_snapshots` table (currently empty)

**Needs:**
```sql
-- Already exists, just needs population
-- monthly_snapshots columns:
-- month_date, total_spent, budget_target, budget_variance,
-- debt_paid_this_month, emergency_fund, etc.
```

### **Backend API:**

```python
# POST /api/snapshots/generate/{month}
# Generates snapshot for specific month (YYYY-MM)
# Example: POST /api/snapshots/generate/2026-02
{
  "month": "2026-02",
  "total_spent": 2134.48,
  "budget_target": 1860,
  "budget_variance": -274.48,
  "spending_by_category": {
    "Groceries": 605.08,
    "Dining": 116.91,
    ...
  },
  "debt_paid": 0,  # Need to track payments separately
  "emergency_fund_balance": 0,
  "on_track": false
}

# POST /api/snapshots/generate-all
# Generates snapshots for all past months (backfill)

# GET /api/snapshots/history
# Returns list of monthly snapshots
[
  {
    "month": "2026-02",
    "total_spent": 2134.48,
    "budget_target": 1860,
    "variance": -274.48,
    "on_track": false
  },
  {
    "month": "2026-01",
    "total_spent": 3200,
    "budget_target": 1860,
    "variance": -1340,
    "on_track": false
  }
]
```

### **Algorithm:**

```python
def generate_monthly_snapshot(month: str, db: Session):
    """
    Generate monthly snapshot
    1. Query all transactions for month
    2. Sum spending by category
    3. Get budget targets for month
    4. Calculate variance
    5. Get debt balances (start vs end)
    6. Get emergency fund balance
    7. Insert into monthly_snapshots
    """
    
    month_start = date.fromisoformat(month + "-01")
    month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
    
    # Get spending
    transactions = db.query(Transaction).filter(
        Transaction.transaction_date >= month_start,
        Transaction.transaction_date <= month_end,
        Transaction.is_debit == True,
        Transaction.category != 'Payment'
    ).all()
    
    total_spent = sum(t.amount for t in transactions)
    
    # Get budget target
    targets = db.query(BudgetTarget).filter(
        BudgetTarget.month == month
    ).all()
    budget_target = sum(t.monthly_target for t in targets)
    
    # Get debt paid (payments made this month)
    debt_payments = db.query(Transaction).filter(
        Transaction.transaction_date >= month_start,
        Transaction.transaction_date <= month_end,
        Transaction.category == 'Payment'
    ).all()
    debt_paid = sum(p.amount for p in debt_payments)
    
    # Get emergency fund
    ef = db.query(EmergencyFund).first()
    ef_balance = ef.current_balance if ef else 0
    
    # Create snapshot
    snapshot = MonthlySnapshot(
        month_date=month_start,
        total_spent=total_spent,
        budget_target=budget_target,
        budget_variance=budget_target - total_spent,
        debt_paid_this_month=debt_paid,
        emergency_fund=ef_balance,
        is_on_track=total_spent <= budget_target
    )
    
    db.add(snapshot)
    db.commit()
    
    return snapshot
```

### **Frontend Component:**

**New section on Dashboard:** `<MonthlySnapshot>`

**Display:**
- Last 6 months in table
- Budget vs Actual for each month
- Trend indicator (↑ over budget, ↓ under budget)
- Link to "View All Months"

### **Automation:**

**Option 1: Cron Job (Preferred)**
```python
# Run monthly on 1st of month at 2am
@cron.schedule("0 2 1 * *")
async def generate_monthly_snapshots():
    # Get last month
    last_month = (date.today() - relativedelta(months=1)).strftime("%Y-%m")
    generate_monthly_snapshot(last_month, db)
```

**Option 2: Manual Trigger**
- Button on dashboard: "Generate This Month's Snapshot"
- Useful for testing, backfilling

### **Quick Win Implementation:**

**Day 1:**
- Implement generate_monthly_snapshot function
- Create API endpoints
- Backfill Feb 2026 snapshot

**Day 2:**
- Build MonthlySnapshot component
- Add to Dashboard
- Test with historical data

---

## 📈 **Feature 4: Progress Dashboard**

### **What it does:**
- Shows current phase progress (Week X of 252)
- Weeks remaining in current phase
- Next milestone
- Overall plan progress (% complete)

### **Database Requirements:**

**Already have:**
- ✅ `weekly_snapshots` table (252 rows)
- ✅ `plan_phases` table (4 phases)
- ✅ `milestones` table (11 milestones)

**Just need to mark current week:**
```sql
-- Update current week status
UPDATE weekly_snapshots SET status = 'current' 
WHERE week_number = (
  SELECT ROUND((julianday('now') - julianday('2026-02-01')) / 7) + 1
);
```

### **Backend API:**

```python
# GET /api/progress
{
  "current_week": 4,
  "total_weeks": 252,
  "percent_complete": 1.6,
  "current_phase": {
    "number": 1,
    "name": "Stop The Bleeding",
    "weeks_elapsed": 4,
    "weeks_total": 26,
    "weeks_remaining": 22,
    "percent_complete": 15.4,
    "end_date": "2026-07-31"
  },
  "next_milestone": {
    "name": "$1,000 Emergency Fund",
    "target_date": "2026-03-01",
    "days_until": 15,
    "progress_percent": 0
  },
  "plan_status": "on_track",  # or "behind", "ahead"
  "weeks_until_debt_free": 18
}
```

### **Frontend Component:**

**New widget on Dashboard:** `<ProgressOverview>`

**Display:**

1. **Phase Progress Bar:**
   ```
   Phase 1: Stop The Bleeding
   [████░░░░░░░░░░░░░░░░] 15% (Week 4 of 26)
   22 weeks remaining • Ends Jul 31, 2026
   ```

2. **Overall Progress:**
   ```
   58-Month Plan Progress
   [█░░░░░░░░░░░░░░░░░░] 1.6% (Week 4 of 252)
   248 weeks remaining • Debt-free: Aug 2027
   ```

3. **Next Milestone:**
   ```
   🎯 Up Next: $1,000 Emergency Fund
   Target: Mar 1, 2026 (15 days)
   Progress: $0 / $1,000 (0%)
   ```

4. **Status Indicator:**
   - Green: "On Track"
   - Yellow: "Behind Schedule"
   - Red: "Significantly Behind"

### **Quick Win Implementation:**

**Day 1:**
- Build API endpoint
- Create ProgressOverview component
- Add to Dashboard (top section)
- Wire up with weekly_snapshots data

---

## 📊 **Feature 5: Spending Trends**

### **What it does:**
- Month-over-month spending comparison
- Category breakdown trends
- "You spent $X more on Y this month"
- Visual charts (line, bar, trend indicators)

### **Database Requirements:**

**Already have:**
- ✅ `transactions` table
- ✅ `monthly_snapshots` (will be populated from Feature 3)

**No new tables needed.**

### **Backend API:**

```python
# GET /api/spending/trends?months=6
{
  "months": ["2026-01", "2026-02"],
  "total_by_month": [
    { "month": "2026-01", "total": 3200 },
    { "month": "2026-02", "total": 2134 }
  ],
  "by_category": [
    {
      "category": "Groceries",
      "trend": [
        { "month": "2026-01", "amount": 800 },
        { "month": "2026-02", "amount": 605 }
      ],
      "change_percent": -24.4,
      "direction": "down"
    },
    {
      "category": "Shopping",
      "trend": [
        { "month": "2026-01", "amount": 150 },
        { "month": "2026-02", "amount": 220 }
      ],
      "change_percent": 46.7,
      "direction": "up"
    }
  ],
  "insights": [
    "Groceries down 24% (saved $195) 👍",
    "Shopping up 47% (+$70) - watch this ⚠️"
  ]
}
```

### **Frontend Component:**

**New page:** `/trends` (or section on Dashboard)

**Sections:**

1. **Total Spending Trend (Line Chart):**
   - X-axis: Months
   - Y-axis: Total spending
   - Overlay: Budget target line (dotted)
   - Show where you were over/under budget

2. **Category Breakdown (Stacked Bar Chart):**
   - Each month = stacked bar
   - Categories color-coded
   - Shows composition change over time

3. **Top Movers Table:**
   - Category | Jan | Feb | Change | %
   - Groceries | $800 | $605 | -$195 | -24% ↓
   - Shopping | $150 | $220 | +$70 | +47% ↑

4. **Insights (Auto-generated):**
   - "You spent $195 less on groceries - great job!"
   - "Shopping increased by 47% - review budget?"
   - "Overall spending down 33% month-over-month 🎉"

### **Quick Win Implementation:**

**Day 1:**
- Build API endpoint
- Query transactions for last N months
- Calculate trends, deltas, percentages
- Add insights logic (simple if/then)
- Create frontend page
- Line chart (Recharts)
- Stacked bar chart (Recharts)
- Top movers table

---

## 🗓️ **Implementation Timeline**

### **Week 1: Core Features**

**Monday-Tuesday:**
- ✅ Debt Payoff Calculator (algorithm + API + frontend)

**Wednesday:**
- ✅ Emergency Fund Tracker (database + API + widget)

**Thursday-Friday:**
- ✅ Monthly Snapshot Generator (backfill + automation)

### **Week 2: Polish & Dashboards**

**Monday:**
- ✅ Progress Dashboard (phase tracker + milestones)

**Tuesday:**
- ✅ Spending Trends (charts + insights)

**Wednesday-Thursday:**
- Integration testing
- Bug fixes
- Performance optimization

**Friday:**
- Deploy all features
- User documentation
- Git commit & backup

---

## 🎯 **Success Metrics**

After implementation, users can answer:

1. ✅ **"When will I be debt-free?"** → Debt Payoff Calculator
2. ✅ **"How's my emergency fund?"** → Emergency Fund Tracker
3. ✅ **"Am I sticking to my budget?"** → Monthly Snapshots
4. ✅ **"How far along am I in the plan?"** → Progress Dashboard
5. ✅ **"Where is my money going?"** → Spending Trends

---

## 📋 **Dependencies**

| Feature | Depends On |
|---------|------------|
| Debt Payoff Calculator | Loans table (✅ done) |
| Emergency Fund Tracker | New table (easy) |
| Monthly Snapshots | Budget targets (✅ done) |
| Progress Dashboard | Weekly snapshots (✅ done) |
| Spending Trends | Transactions (✅ done) |

**All features are independent** - can build in parallel or sequence.

---

## 🔧 **Technical Notes**

**Backend:**
- Python/FastAPI (existing stack)
- SQLAlchemy ORM (existing)
- New endpoints in `/api/debt`, `/api/emergency-fund`, `/api/snapshots`, `/api/progress`, `/api/spending`

**Frontend:**
- React (existing)
- Recharts for charts (already using)
- Tailwind for styling (already using)
- New pages: `/debt-payoff`, `/trends`
- New widgets on Dashboard

**No new dependencies needed!** Use existing stack.

---

## 💡 **Quick Wins First**

**If you have 1 day:**
- Emergency Fund Tracker (highest visible impact)

**If you have 2 days:**
- Add Debt Payoff Calculator (answers biggest question)

**If you have 1 week:**
- All 5 features (full debt crusher suite)

---

**Ready to start? Let me know which feature to build first! 🦙**
