# 🔐 Security Upgrade Required

**Date:** 2026-02-14  
**Priority:** HIGH  
**Action Required:** Update admin password

---

## ⚠️ **Current Password Does Not Meet Security Requirements**

**Your app contains sensitive financial data:**
- Bank account transactions
- Credit card balances  
- Income/spending patterns
- Debt amounts ($85k+ tracked)

**Current password:** `exendice01`  
**Problems:**
- ❌ Only 10 characters (need 12+)
- ❌ No uppercase letters
- ❌ No special characters (!@#$%^&*)

---

## ✅ **What You Need to Do**

### **Step 1: Create a Strong Password**

**Requirements:**
- ✅ At least 12 characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 lowercase letter (a-z)
- ✅ At least 1 number (0-9)
- ✅ At least 1 special character (!@#$%^&*)

**Examples of STRONG passwords:**
- `MyFinance2026!Secure`
- `StopMonkey@2026!`
- `Debt$Free2027!Plan`
- `Budget#Crusher2026`

**Examples of WEAK passwords (DO NOT USE):**
- `password123!` (too common)
- `exendice01!` (too short, all lowercase)
- `Password1!` (only 10 chars)

---

### **Step 2: Update .env File**

Edit: `/home/stopmonkey/monkey/backend/.env`

```bash
# Change this line:
ADMIN_PASSWORD=exendice01

# To something like:
ADMIN_PASSWORD=StopMonkey@2026!
```

**Or use this command:**
```bash
cd /home/stopmonkey/monkey/backend
nano .env
# Update ADMIN_PASSWORD line
# Save: Ctrl+O, Enter, Ctrl+X
```

---

### **Step 3: Recreate Admin User**

**Option A: Recreate database (ONLY if no important data yet)**
```bash
cd /home/stopmonkey/monkey
rm data/stopmonkey.db
docker compose exec backend python -m app.seed.init_db
```

**Option B: Update existing user's password (safer)**
```bash
cd /home/stopmonkey/monkey
docker compose exec backend python << 'EOF'
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password, validate_password

db = SessionLocal()
new_password = "StopMonkey@2026!"  # ← Change this to your new password

# Validate
is_valid, error = validate_password(new_password)
if not is_valid:
    print(f"ERROR: {error}")
else:
    # Update
    user = db.query(User).filter(User.username == "hector").first()
    user.password_hash = hash_password(new_password)
    db.commit()
    print("✅ Password updated successfully!")
db.close()
EOF
```

---

### **Step 4: Verify**

1. Try to log in with **old password** → should fail
2. Try to log in with **new password** → should succeed
3. Visit https://monkey.workez.ai and test login

---

## 🚀 **When This Takes Effect**

**Immediately after Step 3:**
- Old password (`exendice01`) will stop working
- New strong password will be required
- Database seed script will enforce strong passwords for new users

**Next time you run init_db:**
- Will reject weak passwords
- Will show error with requirements
- Forces security best practices

---

## 📋 **What Was Changed in Code**

**New security validation:**
- `/home/stopmonkey/monkey/backend/app/utils/security.py`
  - Added `validate_password()` function
  - Enforces 12+ chars, uppercase, lowercase, number, special char
  - Rejects common passwords

**Updated seed script:**
- `/home/stopmonkey/monkey/backend/app/seed/init_db.py`
  - Now validates admin password before creating user
  - Shows helpful error if password too weak

**Created example:**
- `/home/stopmonkey/monkey/backend/.env.example`
  - Template with password requirements
  - Comments explaining security needs

---

## 🎓 **Password Best Practices**

1. **Never reuse passwords** across different sites
2. **Use a password manager** (1Password, Bitwarden, LastPass)
3. **Change password if leaked** (check haveibeenpwned.com)
4. **Don't share password** (even with trusted people)
5. **Enable 2FA when available** (future feature)

---

## ⚡ **Quick Command (Copy-Paste)**

**To update password RIGHT NOW:**

```bash
cd /home/stopmonkey/monkey

# 1. Update .env file (edit ADMIN_PASSWORD line)
nano backend/.env

# 2. Update existing user
docker compose exec backend python << 'EOF'
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password, validate_password

new_password = input("Enter new strong password (12+ chars): ")
is_valid, error = validate_password(new_password)
if not is_valid:
    print(f"❌ {error}")
else:
    db = SessionLocal()
    user = db.query(User).filter(User.username == "hector").first()
    user.password_hash = hash_password(new_password)
    db.commit()
    print("✅ Password updated successfully!")
    db.close()
EOF
```

---

**Status:** ⚠️ **ACTION REQUIRED**  
**Urgency:** High (app contains sensitive financial data)  
**Time to fix:** 2 minutes

**Fixed by:** ALPACA-AI 🦙  
**Date:** 2026-02-14 15:57 EST
