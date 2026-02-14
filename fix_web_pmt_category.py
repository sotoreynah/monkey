#!/usr/bin/env python3
"""
Reclassify "WEB AUTHORIZED PMT" transactions as Payment category
These are credit card payments, not actual spending
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def find_web_pmt_transactions():
    """Find all WEB AUTHORIZED PMT transactions"""
    print("=" * 100)
    print("FINDING: WEB AUTHORIZED PMT Transactions")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            transaction_date,
            description,
            amount,
            category,
            is_debit
        FROM transactions
        WHERE description LIKE '%WEB AUTHORIZED PMT%'
        ORDER BY transaction_date DESC, amount DESC
    """)
    
    results = cursor.fetchall()
    
    print(f"\nFound {len(results)} transactions:\n")
    print(f"{'ID':<8} {'Date':<12} {'Amount':>12} {'Current Cat':<15} {'Debit?':<8} Description")
    print("-" * 100)
    
    total = 0
    for txn_id, date, desc, amt, cat, is_deb in results:
        debit_flag = "✓" if is_deb else "✗"
        print(f"{txn_id:<8} {date:<12} ${amt:>11,.2f} {cat or '(none)':<15} {debit_flag:<8} {desc[:50]}")
        total += amt
    
    print("-" * 100)
    print(f"{'TOTAL:':<20} ${total:>11,.2f}")
    
    conn.close()
    return results


def apply_fix():
    """Reclassify all WEB AUTHORIZED PMT transactions as Payment category"""
    print("\n" + "=" * 100)
    print("APPLYING FIX")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update category to 'Payment'
    cursor.execute("""
        UPDATE transactions
        SET category = 'Payment'
        WHERE description LIKE '%WEB AUTHORIZED PMT%'
    """)
    
    updated_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated_count} transactions")
    print(f"   Set category = 'Payment' for all WEB AUTHORIZED PMT transactions")
    
    return updated_count


def verify_fix():
    """Show the impact of the fix on September 2025"""
    print("\n" + "=" * 100)
    print("VERIFYING FIX - SEPTEMBER 2025 IMPACT")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate September spending BEFORE fix logic (if we hadn't applied it)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN category != 'Payment' THEN amount ELSE 0 END) as spending_after_fix,
            SUM(CASE WHEN description LIKE '%WEB AUTHORIZED PMT%' THEN amount ELSE 0 END) as pmt_amount,
            COUNT(CASE WHEN description LIKE '%WEB AUTHORIZED PMT%' THEN 1 END) as pmt_count
        FROM transactions
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
    """)
    
    spending_after, pmt_amount, pmt_count = cursor.fetchone()
    
    print(f"\nSeptember 2025:")
    print(f"  WEB AUTHORIZED PMT transactions: {pmt_count} totaling ${pmt_amount:,.2f}")
    print(f"  These are now excluded from spending calculations")
    print(f"\n  Current spending (after fix): ${spending_after:,.2f}")
    print(f"  Previous: $61,997.33")
    print(f"  Reduction: ${61997.33 - spending_after:,.2f}")
    
    # Show breakdown by month
    print("\n" + "=" * 100)
    print("MONTHLY IMPACT")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', transaction_date) as month,
            COUNT(*) as pmt_count,
            SUM(amount) as pmt_total
        FROM transactions
        WHERE description LIKE '%WEB AUTHORIZED PMT%'
          AND is_debit = 1
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    
    monthly = cursor.fetchall()
    
    print(f"\n{'Month':<10} {'Count':>8} {'Payment Amount':>18}")
    print("-" * 40)
    for month, count, total in monthly:
        print(f"{month:<10} {count:>8} ${total:>17,.2f}")
    
    conn.close()


def main():
    print("\n" + "🔧" * 50)
    print(" FIX: Reclassify WEB AUTHORIZED PMT as Payment Category")
    print("🔧" * 50 + "\n")
    
    # Show what will be changed
    results = find_web_pmt_transactions()
    
    if not results:
        print("\n✅ No WEB AUTHORIZED PMT transactions found!")
        return
    
    # Confirm
    print("\n⚠️  Ready to reclassify these as category='Payment'")
    response = input("Proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        updated = apply_fix()
        verify_fix()
        
        print("\n" + "=" * 100)
        print("NEXT STEPS:")
        print("  1. Refresh dashboard - September should now show realistic spending")
        print("  2. Check Robinhood transaction with bank")
        print("  3. If duplicate confirmed, we'll remove it")
        print("=" * 100 + "\n")
    else:
        print("\n❌ Fix cancelled")


if __name__ == "__main__":
    main()
