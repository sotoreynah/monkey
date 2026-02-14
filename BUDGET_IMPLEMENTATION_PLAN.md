# Budget/Debt Crusher Implementation Plan

## 🚨 **Current State: Budget Page is Non-Functional**

**Problem:** Budget targets table is empty, so `/budget` shows nothing useful.

---

## 📋 **Gap Analysis: What's Missing**

### ✅ **What EXISTS:**
- Financial plan framework (252 weeks, 4 phases)
- Weekly snapshots structure (252 rows created)
- Milestone tracking table (11 milestones defined)
- Some loans tracked (Affirm BNPLs, mortgage, remodel loan)
- Transaction categorization working

### ❌ **What's MISSING:**

#### 1. **Budget Targets (Critical)**
- `budget_targets` table is **EMPTY** ← This breaks `/budget` page
- Need Phase 1 targets based on "Stop the Monkey" plan:
  - Groceries: $700/mo
  - Dining: $150/mo
  - Shopping: $100/mo
  - Travel: $100/mo
  - Entertainment: $100/mo
  - Fitness: $150/mo
  - etc.

#### 2. **Debt Tracking (Critical)**
- Missing credit cards:
  - Credit Card 6032 (US Bank)
  - AMEX
  - Apple Card
  - Wells Fargo CC
  - JPMorgan Chase
- Missing auto loans:
  - German American Bank ($2,762/mo)
  - VW Credit ($509/mo)
  - Santander ($420/mo)
  - Tesla ($775/mo)

#### 3. **Monthly Snapshot Generation**
- `monthly_snapshots` table is **EMPTY**
- No monthly budget vs actual comparison
- No month-over-month progress tracking

#### 4. **Debt Payoff Calculator**
- No "debt avalanche" visualization
- No payoff timeline calculator
- No interest savings calculator

#### 5. **Emergency Fund Tracker**
- No emergency fund goal tracking
- Baby Step 1: $1,000 starter fund
- Baby Step 3: $156,000 (12 months)

#### 6. **Progress Dashboard**
- No "Phase Progress" visualization
- No "Weeks Until Debt-Free" countdown
- No "Interest Saved" tracker

#### 7. **Budget Management UI**
- Can't edit budget targets from UI
- Can't adjust categories
- No manual transaction categorization

---

## 🎯 **Implementation Roadmap**

### **Phase 1: Make Budget Page Functional (Priority 1)**

#### Task 1.1: Populate Budget Targets
Create initial Phase 1 targets from "Stop the Monkey" plan:

```sql
INSERT INTO budget_targets (phase_number, category, monthly_target, is_fixed, notes) VALUES
  -- Fixed (cannot cut)
  (1, 'Mortgage', 3712, 1, 'Locked in at 6.99%'),
  (1, 'Payment', 8178, 1, 'Auto loans + BNPL + remodel'),
  
  -- Discretionary (Phase 1 targets)
  (1, 'Groceries', 700, 0, 'Switch to Kroger/Costco from Whole Foods'),
  (1, 'Dining', 150, 0, 'Max 2 meals out per month'),
  (1, 'Shopping', 100, 0, '30-day rule on purchases'),
  (1, 'Entertainment', 100, 0, 'No concerts/events over $50'),
  (1, 'Transportation', 100, 0, 'Eliminate leisure travel'),
  (1, 'Services', 60, 0, 'Keep 3 subscriptions max'),
  (1, 'Utilities', 200, 0, 'Internet, phone, etc'),
  (1, 'Health', 150, 0, 'Medical/fitness - pick ONE gym'),
  (1, 'Cash', 100, 0, 'Envelope system'),
  (1, 'Other', 200, 0, 'Miscellaneous');
```

#### Task 1.2: Add Missing Debts to Loans Table

```sql
-- Credit Cards (need actual balances)
INSERT INTO loans (name, loan_type, creditor, current_balance, interest_rate, monthly_payment, priority_rank) VALUES
  ('Credit Card 6032', 'credit_card', 'US Bank', 0, 0.22, 0, 1),
  ('AMEX', 'credit_card', 'American Express', 5742, 0.2241, 0, 2),
  ('Apple Card', 'credit_card', 'Goldman Sachs', 0, 0.1999, 0, 3),
  ('Wells Fargo CC', 'credit_card', 'Wells Fargo', 0, 0.20, 0, 4),
  ('JPMorgan Chase', 'credit_card', 'Chase', 0, 0.20, 0, 5);

-- Auto Loans
INSERT INTO loans (name, loan_type, creditor, current_balance, interest_rate, monthly_payment, priority_rank) VALUES
  ('German American Bank', 'auto', 'German American', 0, 0.06, 2762, 10),
  ('VW Credit', 'auto', 'VW Credit', 0, 0.05, 509, 9),
  ('Santander', 'auto', 'Santander Consumer', 0, 0.06, 420, 8),
  ('Tesla', 'auto', 'Tesla Finance', 0, 0.04, 775, 7);
```

#### Task 1.3: Create Budget Management API

```python
# New endpoints needed:
POST /api/budget/targets       # Create/update budget targets
GET  /api/budget/targets       # List all targets for a phase
DELETE /api/budget/targets/:id # Remove a target

POST /api/budget/recalculate   # Regenerate monthly snapshots
```

---

### **Phase 2: Debt Crusher Features (Priority 2)**

#### Task 2.1: Debt Avalanche Calculator

**Endpoint:** `GET /api/debt/payoff-plan`

**Returns:**
```json
{
  "current_debt": {
    "total_balance": 85000,
    "total_monthly_payment": 1500,
    "total_interest_rate": 0.18
  },
  "payoff_order": [
    {
      "rank": 1,
      "name": "Credit Card 6032",
      "balance": 5000,
      "rate": 0.25,
      "payment": 200,
      "months_to_payoff": 8,
      "interest_paid": 450
    }
  ],
  "timeline": {
    "months_to_debt_free": 24,
    "total_interest_paid": 8500,
    "total_interest_saved": 15000
  }
}
```

#### Task 2.2: Monthly Snapshot Generator

**Cronjob:** Run monthly to calculate:
- Month's total spending by category
- Budget vs actual variance
- Debt paydown progress
- Emergency fund balance

#### Task 2.3: Emergency Fund Tracker

**Endpoint:** `GET /api/emergency-fund`

**Returns:**
```json
{
  "current_step": 1,
  "target_step_1": 1000,
  "target_step_3": 156000,
  "current_balance": 0,
  "months_of_expenses": 0,
  "progress_percent": 0
}
```

---

### **Phase 3: Progress Visualization (Priority 3)**

#### Task 3.1: Phase Progress Widget

**Frontend Component:**
```jsx
<PhaseProgress 
  currentPhase={1}
  currentWeek={4}
  totalWeeks={252}
  monthsRemaining={54}
  onTrack={true}
/>
```

#### Task 3.2: Debt Payoff Chart

Line chart showing:
- Total debt over time (actual + projected)
- Phase milestones (vertical lines)
- "Debt-free" target date

#### Task 3.3: Budget vs Actual Chart

Bar chart by category:
- Green bars: under budget
- Red bars: over budget
- Target line overlay

---

### **Phase 4: Management UI (Priority 4)**

#### Task 4.1: Edit Budget Targets

Allow user to:
- Add new category targets
- Adjust amounts for each phase
- Mark categories as fixed vs discretionary

#### Task 4.2: Manual Transaction Categorization

Allow user to:
- Recategorize individual transactions
- Bulk recategorize by merchant
- Create category mapping rules

#### Task 4.3: Debt Management

Allow user to:
- Add/edit/delete loans
- Update balances manually
- Mark loans as paid off
- Reorder payoff priority

---

## 🚀 **Quick Win: Make Budget Page Work Today**

### **Step 1:** Populate budget_targets table (5 minutes)
### **Step 2:** Verify `/api/budget` returns data (2 minutes)
### **Step 3:** Add debt balances to loans table (5 minutes)
### **Step 4:** Create simple frontend for editing targets (30 minutes)

**Total time to functional budget page:** ~45 minutes

---

## 📊 **Success Metrics**

After implementation:
- ✅ Budget page shows actual vs target by category
- ✅ User can see monthly spending variance
- ✅ Debt payoff timeline is visible
- ✅ Emergency fund progress is tracked
- ✅ Phase milestones show completion status
- ✅ User can adjust budget targets
- ✅ Monthly snapshots auto-generate

---

## 🎯 **Next Steps**

1. **Populate budget targets** (Phase 1 values from plan)
2. **Add missing debt accounts** (credit cards + auto loans)
3. **Generate monthly snapshots** (historical + current)
4. **Build debt payoff calculator** (avalanche visualization)
5. **Create progress dashboard** (phase tracker + charts)
6. **Add management UI** (edit targets, categorize txns)

---

**Want me to start with Step 1 (populate budget targets)?** This will make the budget page immediately functional. 🦙
