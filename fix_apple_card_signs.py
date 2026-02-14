#!/usr/bin/env python3
"""
Fix Apple Card sign inversion issue
Flip is_debit flag for transactions that are incorrectly marked as credits
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def analyze_before_fix():
    """Show current state before fix"""
    print("=" * 80)
    print("BEFORE FIX - September 2025 Apple Card")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_debit = 1 THEN 1 END) as debits,
            COUNT(CASE WHEN is_debit = 0 THEN 1 END) as credits,
            SUM(CASE WHEN is_debit = 1 THEN amount ELSE 0 END) as debit_total,
            SUM(CASE WHEN is_debit = 0 THEN amount ELSE 0 END) as credit_total
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE s.name = 'Apple Card'
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
    """)
    
    total, deb_count, cred_count, deb_total, cred_total = cursor.fetchone()
    
    print(f"\nTotal transactions: {total}")
    print(f"  Debits (is_debit=1):  {deb_count} = ${deb_total:,.2f}")
    print(f"  Credits (is_debit=0): {cred_count} = ${cred_total:,.2f}")
    
    conn.close()


def fix_apple_card_signs():
    """
    Fix Apple Card transactions where is_debit flag is wrong
    
    Logic:
    - Payments to card (ACH DEPOSIT, etc.) should be is_debit=0 ✓
    - Purchases, Interest, Fees should be is_debit=1
    """
    print("\n" + "=" * 80)
    print("FIXING Apple Card Transactions")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find Apple Card source ID
    cursor.execute("SELECT id FROM transaction_sources WHERE name = 'Apple Card'")
    apple_id = cursor.fetchone()[0]
    
    # Find transactions that are incorrectly marked as credits
    # These should be debits: purchases, interest, installments, fees
    cursor.execute("""
        SELECT id, transaction_date, description, amount, category
        FROM transactions
        WHERE source_id = ?
          AND is_debit = 0
          AND (
            transaction_type IN ('purchase', 'interest', 'installment', 'fee', 'other')
            OR description LIKE '%APPLE ONLINE STORE%'
            OR description LIKE '%MONTHLY INSTALLMENT%'
            OR description LIKE '%INTEREST CHARGE%'
            OR description NOT LIKE '%DEPOSIT%'
            AND description NOT LIKE '%PAYMENT%'
            AND description NOT LIKE '%ACH%'
            AND category != 'Payment'
          )
    """, (apple_id,))
    
    to_fix = cursor.fetchall()
    
    print(f"\nFound {len(to_fix)} transactions to fix:")
    print(f"\n{'ID':<8} {'Date':<12} {'Amount':>12} {'Category':<12} Description")
    print("-" * 80)
    
    total_to_flip = 0
    for txn_id, date, desc, amt, cat in to_fix:
        print(f"{txn_id:<8} {date:<12} ${amt:>11,.2f} {cat or '?':<12} {desc[:40]}")
        total_to_flip += amt
    
    print("-" * 80)
    print(f"{'TOTAL TO FLIP:':<20} ${total_to_flip:>11,.2f}")
    
    # Apply the fix
    print("\n⚠️  Ready to flip is_debit flag for these transactions")
    response = input("Proceed with fix? (yes/no): ")
    
    if response.lower() == 'yes':
        ids_to_fix = [txn[0] for txn in to_fix]
        cursor.execute(f"""
            UPDATE transactions
            SET is_debit = 1
            WHERE id IN ({','.join(['?'] * len(ids_to_fix))})
        """, ids_to_fix)
        
        conn.commit()
        print(f"\n✅ Fixed {len(to_fix)} transactions!")
        print(f"   Flipped is_debit from 0 → 1 for Apple Card purchases/fees")
    else:
        print("\n❌ Fix cancelled")
    
    conn.close()


def analyze_after_fix():
    """Show state after fix"""
    print("\n" + "=" * 80)
    print("AFTER FIX - September 2025 Apple Card")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_debit = 1 THEN 1 END) as debits,
            COUNT(CASE WHEN is_debit = 0 THEN 1 END) as credits,
            SUM(CASE WHEN is_debit = 1 THEN amount ELSE 0 END) as debit_total,
            SUM(CASE WHEN is_debit = 0 THEN amount ELSE 0 END) as credit_total
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE s.name = 'Apple Card'
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
    """)
    
    total, deb_count, cred_count, deb_total, cred_total = cursor.fetchone()
    
    print(f"\nTotal transactions: {total}")
    print(f"  Debits (is_debit=1):  {deb_count} = ${deb_total:,.2f}")
    print(f"  Credits (is_debit=0): {cred_count} = ${cred_total:,.2f}")
    
    # Show September totals
    print("\n" + "=" * 80)
    print("SEPTEMBER 2025 - RECALCULATED SPENDING")
    print("=" * 80)
    
    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
          AND category != 'Payment'
    """)
    
    sept_total = cursor.fetchone()[0]
    
    print(f"\nSeptember spending (excluding payments): ${sept_total:,.2f}")
    print(f"  Previous: $60,622.19")
    print(f"  Difference: ${sept_total - 60622.19:,.2f}")
    
    conn.close()


def main():
    print("\n" + "🔧" * 40)
    print(" APPLE CARD SIGN FIX - INTERACTIVE")
    print("🔧" * 40 + "\n")
    
    analyze_before_fix()
    fix_apple_card_signs()
    analyze_after_fix()
    
    print("\n" + "=" * 80)
    print("NEXT: Refresh dashboard to see corrected September numbers!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
