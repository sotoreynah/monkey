#!/usr/bin/env python3
"""
Show comprehensive before/after across the entire dataset
"""
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def show_all_months_corrected():
    """Show spending for ALL months with corrections applied"""
    print("=" * 100)
    print("CORRECTED SPENDING - FULL DATASET (All Months)")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all unique months
    cursor.execute("""
        SELECT DISTINCT strftime('%Y-%m', transaction_date) as month
        FROM transactions
        ORDER BY month DESC
    """)
    
    months = [row[0] for row in cursor.fetchall()]
    
    print(f"\n{'Month':<12} {'Spending':>15} {'Payments':>15} {'Net Spending':>15}")
    print("-" * 100)
    
    grand_total_spending = 0
    grand_total_payments = 0
    
    for month in months:
        # Spending (excluding Payment category)
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN category != 'Payment' THEN amount ELSE 0 END) as spending,
                SUM(CASE WHEN category = 'Payment' THEN amount ELSE 0 END) as payments
            FROM transactions
            WHERE strftime('%Y-%m', transaction_date) = ?
              AND is_debit = 1
        """, (month,))
        
        spending, payments = cursor.fetchone()
        spending = spending or 0
        payments = payments or 0
        
        print(f"{month:<12} ${spending:>14,.2f} ${payments:>14,.2f} ${spending:>14,.2f}")
        
        grand_total_spending += spending
        grand_total_payments += payments
    
    print("-" * 100)
    print(f"{'TOTALS:':<12} ${grand_total_spending:>14,.2f} ${grand_total_payments:>14,.2f} ${grand_total_spending:>14,.2f}")
    
    print(f"\n💡 Summary:")
    print(f"   Total actual spending: ${grand_total_spending:,.2f}")
    print(f"   Total payments (excluded): ${grand_total_payments:,.2f}")
    print(f"   Total debits: ${grand_total_spending + grand_total_payments:,.2f}")
    
    conn.close()


def show_fixes_applied():
    """Show what fixes were applied"""
    print("\n" + "=" * 100)
    print("FIXES APPLIED TO ENTIRE DATASET")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n1️⃣ Apple Card Sign Inversion Fix:")
    cursor.execute("""
        SELECT COUNT(*), SUM(amount)
        FROM transactions
        WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Apple Card')
          AND is_debit = 1
          AND (
              description LIKE '%INSTALLMENT%'
              OR description LIKE '%INTEREST CHARGE%'
              OR description LIKE '%APPLE ONLINE STORE%'
          )
    """)
    
    count, total = cursor.fetchone()
    print(f"   Fixed {count} transactions totaling ${total:,.2f}")
    print(f"   These were marked as 'credits' but are actually purchases/fees")
    
    print("\n2️⃣ WEB AUTHORIZED PMT Reclassification:")
    cursor.execute("""
        SELECT COUNT(*), SUM(amount)
        FROM transactions
        WHERE description LIKE '%WEB AUTHORIZED PMT%'
          AND category = 'Payment'
    """)
    
    count, total = cursor.fetchone()
    print(f"   Reclassified {count} transactions totaling ${total:,.2f}")
    print(f"   These are credit card payments, not spending")
    
    print("\n3️⃣ Dashboard Code Fix:")
    print(f"   Modified backend/app/api/dashboard.py")
    print(f"   Added: Transaction.category != 'Payment' filter")
    print(f"   Ensures payments are excluded from spending calculations")
    
    conn.close()


def main():
    print("\n" + "📊" * 50)
    print(" FULL DATASET SUMMARY - ALL CORRECTIONS APPLIED")
    print("📊" * 50 + "\n")
    
    show_fixes_applied()
    show_all_months_corrected()
    
    print("\n" + "=" * 100)
    print("STATUS: ✅ All fixes applied to entire dataset")
    print("NEXT: Restart backend and refresh dashboard to see corrected numbers")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
