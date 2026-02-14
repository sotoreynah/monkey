#!/usr/bin/env python3
"""
Deep dive into Apple Card credits to understand the sign issue
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def show_apple_card_credits():
    """Show ALL Apple Card transactions marked as credits (is_debit=0)"""
    print("=" * 100)
    print("APPLE CARD - ALL CREDITS (is_debit=0) IN SEPTEMBER 2025")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            transaction_date,
            description,
            amount,
            is_debit,
            category,
            transaction_type,
            CASE 
                WHEN description LIKE '%PAYMENT%' THEN 'Payment?'
                WHEN description LIKE '%DEPOSIT%' THEN 'Payment?'
                WHEN description LIKE '%INTEREST%' THEN 'Interest/Fee?'
                ELSE 'Purchase?'
            END as likely_type
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE s.name = 'Apple Card'
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
          AND t.is_debit = 0
        ORDER BY amount DESC
    """)
    
    credits = cursor.fetchall()
    
    print(f"\n{'Date':<12} {'Amount':>12} {'Category':<12} {'Type':<10} {'Likely':<12} Description")
    print("-" * 100)
    
    total = 0
    for date, desc, amt, is_deb, cat, txn_type, likely in credits:
        print(f"{date:<12} ${amt:>11,.2f} {cat or '?':<12} {txn_type or '?':<10} {likely:<12} {desc[:60]}")
        total += amt
    
    print("-" * 100)
    print(f"{'TOTAL:':<12} ${total:>11,.2f}")
    
    print(f"\n💡 INTERPRETATION:")
    print(f"   These {len(credits)} transactions are marked is_debit=0 (CREDITS)")
    print(f"   But they have POSITIVE amounts (${total:,.2f})")
    print(f"   ")
    print(f"   🤔 Question: In Apple Card CSVs, are PURCHASES positive or negative?")
    print(f"   If purchases are NEGATIVE, then is_debit flag might be inverted!")
    
    conn.close()


def show_apple_card_debits():
    """Show sample Apple Card transactions marked as debits (is_debit=1)"""
    print("\n" + "=" * 100)
    print("APPLE CARD - SAMPLE DEBITS (is_debit=1) IN SEPTEMBER 2025")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            transaction_date,
            description,
            amount,
            is_debit,
            category,
            transaction_type
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE s.name = 'Apple Card'
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
          AND t.is_debit = 1
        ORDER BY amount DESC
        LIMIT 15
    """)
    
    debits = cursor.fetchall()
    
    print(f"\n{'Date':<12} {'Amount':>12} {'Category':<12} {'Type':<10} Description")
    print("-" * 100)
    
    for date, desc, amt, is_deb, cat, txn_type in debits:
        print(f"{date:<12} ${amt:>11,.2f} {cat or '?':<12} {txn_type or '?':<10} {desc[:60]}")
    
    print(f"\n💡 THESE LOOK LIKE ACTUAL PURCHASES (correct!)")
    
    conn.close()


def compare_to_other_source():
    """Compare to another credit card to see the pattern"""
    print("\n" + "=" * 100)
    print("COMPARISON: APPLE CARD vs AMEX (September 2025)")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for source_name in ['Apple Card', 'AMEX']:
        print(f"\n📊 {source_name}:")
        print("-" * 100)
        
        # Count debits vs credits
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN is_debit = 1 THEN 1 END) as debit_count,
                COUNT(CASE WHEN is_debit = 0 THEN 1 END) as credit_count,
                SUM(CASE WHEN is_debit = 1 THEN amount ELSE 0 END) as debit_total,
                SUM(CASE WHEN is_debit = 0 THEN amount ELSE 0 END) as credit_total
            FROM transactions t
            JOIN transaction_sources s ON t.source_id = s.id
            WHERE s.name = ?
              AND t.transaction_date >= '2025-09-01'
              AND t.transaction_date <= '2025-09-30'
        """, (source_name,))
        
        deb_count, cred_count, deb_total, cred_total = cursor.fetchone()
        
        print(f"   Debits (is_debit=1):  {deb_count:>3} transactions = ${deb_total:>12,.2f}")
        print(f"   Credits (is_debit=0): {cred_count:>3} transactions = ${cred_total:>12,.2f}")
        
        # Sample credit transactions
        cursor.execute("""
            SELECT description, amount, category
            FROM transactions t
            JOIN transaction_sources s ON t.source_id = s.id
            WHERE s.name = ?
              AND t.transaction_date >= '2025-09-01'
              AND t.transaction_date <= '2025-09-30'
              AND t.is_debit = 0
            ORDER BY amount DESC
            LIMIT 3
        """, (source_name,))
        
        sample_credits = cursor.fetchall()
        
        if sample_credits:
            print(f"\n   Sample 'credits' (is_debit=0):")
            for desc, amt, cat in sample_credits:
                print(f"      ${amt:>10,.2f} | {cat or '?':<12} | {desc[:50]}")
    
    conn.close()


def main():
    print("\n" + "🔍" * 50)
    print(" DETAILED APPLE CARD ANALYSIS")
    print("🔍" * 50 + "\n")
    
    show_apple_card_credits()
    show_apple_card_debits()
    compare_to_other_source()
    
    print("\n" + "=" * 100)
    print("DIAGNOSIS:")
    print("=" * 100)
    print("""
Based on the data above, here's what to check:

1. Look at the 'credits' (is_debit=0) for Apple Card
2. Do they look like actual INCOME/PAYMENTS to the card?
   OR do they look like PURCHASES that were mis-labeled?

3. If the 'credits' are actually PURCHASES:
   → The is_debit flag is inverted for Apple Card!
   → Need to flip is_debit for all Apple Card transactions

4. Typical pattern for credit cards:
   - Purchases = is_debit=1 (spending money)
   - Payments = is_debit=0 (paying off the card)
   
Let me know what you see in the Apple Card 'credits' above!
    """)
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
