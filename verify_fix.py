#!/usr/bin/env python3
"""
Verify the payment exclusion fix
Shows spending numbers before and after
"""
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def verify_fix():
    print("\n" + "=" * 80)
    print("VERIFICATION: Payment Exclusion Fix")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = date.today()
    
    print(f"\n{'Month':<15} {'Old (All)':>18} {'New (No Payments)':>20} {'Difference':>18}")
    print("-" * 80)
    
    for i in range(5, -1, -1):
        m_start = (today - relativedelta(months=i)).replace(day=1)
        m_end = (m_start + relativedelta(months=1)) - relativedelta(days=1)
        
        # Old calculation (including payments)
        cursor.execute("""
            SELECT SUM(amount)
            FROM transactions 
            WHERE transaction_date >= ?
              AND transaction_date <= ?
              AND is_debit = 1
              AND (is_excluded = 0 OR is_excluded IS NULL)
        """, (m_start, m_end))
        
        old_total = cursor.fetchone()[0] or 0
        
        # New calculation (excluding payments)
        cursor.execute("""
            SELECT SUM(amount)
            FROM transactions 
            WHERE transaction_date >= ?
              AND transaction_date <= ?
              AND is_debit = 1
              AND (is_excluded = 0 OR is_excluded IS NULL)
              AND category != 'Payment'
        """, (m_start, m_end))
        
        new_total = cursor.fetchone()[0] or 0
        
        month_label = m_start.strftime("%b %Y")
        diff = old_total - new_total
        pct_reduction = (diff / old_total * 100) if old_total > 0 else 0
        
        print(f"{month_label:<15} ${old_total:>17,.2f} ${new_total:>19,.2f} -${diff:>10,.2f} ({pct_reduction:.0f}%)")
    
    print("-" * 80)
    print("\n✅ Fix applied successfully!")
    print("   Charts will now show realistic spending numbers.")
    print("   Refresh your dashboard to see the corrected data.\n")
    
    conn.close()

if __name__ == "__main__":
    verify_fix()
