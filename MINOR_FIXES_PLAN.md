# Minor Fixes - Pre-Data Features

**Priority:** Fix these BEFORE building new features  
**Time:** ~2 hours total

---

## 🔧 **Fix A: Navigation Consistency**

### **Issue:**
- Top menu: "IMPORT"
- Page header: "UPLOAD CSV"
- Inconsistent terminology

### **Also:**
- Bottom nav icons on Dashboard - are they necessary?

### **Fix:**

**Option 1: Standardize on "Import"**
- Menu: "Import" ✅
- Page: "Import Data" ✅
- Consistent, professional

**Option 2: Standardize on "Upload"**
- Menu: "Upload"
- Page: "Upload CSV"

**Recommendation:** Use "Import" (more professional than "Upload")

**Bottom Nav Icons:**
- Check Dashboard for unnecessary navigation clutter
- If they duplicate top menu → remove
- If they provide quick actions → keep

**Files to change:**
- `frontend/src/components/Navigation.jsx` (menu labels)
- `frontend/src/pages/Import.jsx` (page header)
- `frontend/src/pages/Dashboard.jsx` (check bottom icons)

---

## 📊 **Fix B: Dashboard Chart Target Line**

### **Issue:**
- Monthly spending trend chart shows green "Target" line
- Line appears too low or at zero
- Problem: Budget targets change month-to-month (Feb ≠ Mar)
- Current implementation likely uses static value

### **Root Cause:**
```javascript
// Current (WRONG):
const targetLine = 1860; // Static Phase 1 value

// Should be (RIGHT):
const targetLine = budgetTargets[month]; // Dynamic per month
```

### **Fix:**

**Backend:**
- API already returns correct targets per month ✅
- Just need frontend to use them correctly

**Frontend Fix:**
```javascript
// In Dashboard.jsx
const chartData = monthlyData.map(month => ({
  month: month.name,
  spending: month.total_spent,
  target: month.budget_target,  // ← Use month-specific target
  variance: month.budget_variance
}))

// In Recharts:
<Line 
  type="monotone" 
  dataKey="target" 
  stroke="#22c55e" 
  strokeDasharray="5 5" 
  name="Budget Target"
/>
```

### **Also Check:**
- If no budget targets exist for a month, show message instead of zero line
- Label should say "Budget Target" not just "Target"
- Tooltip should show both spending and target with variance

**File to change:**
- `frontend/src/pages/Dashboard.jsx` (chart data mapping)

---

## 🔐 **Fix C: Password Security**

### **Issue:**
- Current password requirements too weak
- App contains sensitive financial data:
  - Bank account transactions
  - Credit card balances
  - Income/spending patterns
  - Debt amounts
- Simple password = security risk

### **Current State:**
Check what's required now (probably just length?)

### **Required Fix:**

**Minimum password requirements:**
1. ✅ At least 12 characters (not 8)
2. ✅ At least 1 uppercase letter
3. ✅ At least 1 lowercase letter
4. ✅ At least 1 number
5. ✅ At least 1 special character (!@#$%^&*)
6. ✅ Not a common password (check against list)

**Backend validation:**
```python
# backend/app/api/auth.py or user.py

import re

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    # Common passwords (add more as needed)
    common_passwords = [
        "password123", "123456789", "qwerty123", 
        "admin123", "letmein123", "welcome123"
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common, please choose a stronger one"
    
    return True, ""

# In create_user / update_password endpoint:
is_valid, error = validate_password(password)
if not is_valid:
    raise HTTPException(status_code=400, detail=error)
```

**Frontend validation:**
```javascript
// frontend/src/pages/Login.jsx or Register.jsx

const validatePassword = (password) => {
  const requirements = {
    length: password.length >= 12,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  }
  
  const errors = []
  if (!requirements.length) errors.push("At least 12 characters")
  if (!requirements.uppercase) errors.push("One uppercase letter")
  if (!requirements.lowercase) errors.push("One lowercase letter")
  if (!requirements.number) errors.push("One number")
  if (!requirements.special) errors.push("One special character (!@#$%^&*)")
  
  return {
    isValid: errors.length === 0,
    errors,
    strength: Object.values(requirements).filter(Boolean).length
  }
}

// Show password strength indicator:
// ▓▓▓▓▓ Strong (5/5)
// ▓▓▓▓░ Good (4/5)
// ▓▓▓░░ Fair (3/5)
// ▓▓░░░ Weak (2/5)
// ▓░░░░ Very Weak (1/5)
```

**UI Improvements:**
1. **Password strength meter** (visual feedback as user types)
2. **Show/hide password toggle** (eye icon)
3. **Password requirements checklist** (✓ green, ✗ red)
   - ✓ At least 12 characters
   - ✗ One uppercase letter
   - ✗ One number
   - etc.

**Additional Security:**
- ✅ Hash passwords with bcrypt (likely already done)
- ✅ Add rate limiting on login attempts (5 attempts → lockout)
- ✅ Session timeout after 30 minutes inactivity
- ✅ Force password change on first login
- ⚠️ Consider 2FA for future (not now, but plan for it)

**Files to change:**
- `backend/app/api/auth.py` or `backend/app/models/user.py` (validation)
- `frontend/src/pages/Login.jsx` (registration form)
- `frontend/src/components/PasswordInput.jsx` (new component with strength meter)

---

## 📋 **Implementation Checklist**

### **Fix A: Navigation Consistency (15 min)**
- [ ] Change menu label "IMPORT" → "Import"
- [ ] Change page header to "Import Data"
- [ ] Check Dashboard for bottom nav icons
- [ ] Remove if they duplicate top menu
- [ ] Test navigation flow

### **Fix B: Chart Target Line (30 min)**
- [ ] Update Dashboard chart data mapping
- [ ] Use month-specific budget targets
- [ ] Handle months with no targets (show message)
- [ ] Update tooltip to show variance
- [ ] Test with Feb & Mar data

### **Fix C: Password Security (1 hour)**
- [ ] Add password validation function (backend)
- [ ] Update user creation endpoint
- [ ] Add frontend validation
- [ ] Build password strength meter component
- [ ] Add show/hide toggle
- [ ] Add requirements checklist UI
- [ ] Test with weak passwords (should reject)
- [ ] Test with strong passwords (should accept)
- [ ] Update existing users? (optional: force password change)

---

## 🚀 **Deploy Order**

1. **Fix C (Security)** - Most important, do first
2. **Fix B (Chart)** - User-facing bug, do second
3. **Fix A (Navigation)** - Polish, do last

**Total time:** ~2 hours before starting Feature 1

---

## 🧪 **Testing**

### **Fix A:**
- [ ] Navigate to Import page
- [ ] Check menu label matches page header
- [ ] Verify no broken links

### **Fix B:**
- [ ] View Dashboard
- [ ] Check Monthly Spending chart
- [ ] Verify green line shows correct budget target
- [ ] Switch to different month
- [ ] Verify line updates to new target

### **Fix C:**
- [ ] Try to register with "password123" → should fail
- [ ] Try to register with "Pass123!" (11 chars) → should fail (too short)
- [ ] Try to register with "Password123!" → should succeed
- [ ] Verify strength meter shows feedback
- [ ] Verify checklist updates as user types

---

**Ready to fix these now before building new features? 🦙**
