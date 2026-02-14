#!/usr/bin/env python3
"""
Comprehensive analysis of ALL transaction sources in September 2025
Find sign inversions, payment miscategorizations, and other issues
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def analyze_all_sources_september():
    """Deep analysis of each source for September 2025"""
    print("=" * 120)
    print("COMPREHENSIVE SOURCE ANALYSIS - SEPTEMBER 2025")
    print("=" * 120)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all sources
    cursor.execute("SELECT id, name, type FROM transaction_sources ORDER BY name")
    sources = cursor.fetchall()
    
    total_all_debits = 0
    total_all_credits = 0
    
    for source_id, source_name, source_type in sources:
        print(f"\n{'='*120}")
        print(f"SOURCE: {source_name} ({source_type or '?'})")
        print(f"{'='*120}")
        
        # Overall stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_debit = 1 THEN 1 END) as debit_count,
                COUNT(CASE WHEN is_debit = 0 THEN 1 END) as credit_count,
                SUM(CASE WHEN is_debit = 1 THEN amount ELSE 0 END) as debit_total,
                SUM(CASE WHEN is_debit = 0 THEN amount ELSE 0 END) as credit_total
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
        """, (source_id,))
        
        total, deb_count, cred_count, deb_total, cred_total = cursor.fetchone()
        
        if total == 0:
            print("   No transactions in September 2025")
            continue
        
        print(f"\nTransactions: {total}")
        print(f"  Debits (is_debit=1):  {deb_count:>3} = ${deb_total:>12,.2f}")
        print(f"  Credits (is_debit=0): {cred_count:>3} = ${cred_total:>12,.2f}")
        print(f"  Net: ${deb_total - cred_total:>12,.2f}")
        
        total_all_debits += deb_total
        total_all_credits += cred_total
        
        # Sample debits (should be purchases)
        cursor.execute("""
            SELECT transaction_date, description, amount, category
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
              AND is_debit = 1
            ORDER BY amount DESC
            LIMIT 5
        """, (source_id,))
        
        debits = cursor.fetchall()
        if debits:
            print(f"\n  Sample DEBITS (is_debit=1) - Should be purchases/spending:")
            for date, desc, amt, cat in debits:
                print(f"    {date} | ${amt:>10,.2f} | {cat or '?':<15} | {desc[:60]}")
        
        # Sample credits (should be payments TO the account)
        cursor.execute("""
            SELECT transaction_date, description, amount, category
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
              AND is_debit = 0
            ORDER BY amount DESC
            LIMIT 5
        """, (source_id,))
        
        credits = cursor.fetchall()
        if credits:
            print(f"\n  Sample CREDITS (is_debit=0) - Should be payments/income:")
            for date, desc, amt, cat in credits:
                looks_right = "✓" if any(x in desc.upper() for x in ['PAYMENT', 'DEPOSIT', 'TRANSFER', 'REFUND']) else "⚠️"
                print(f"    {looks_right} {date} | ${amt:>10,.2f} | {cat or '?':<15} | {desc[:60]}")
        
        # Check for red flags
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN is_debit = 0 AND description NOT LIKE '%PAYMENT%' 
                           AND description NOT LIKE '%DEPOSIT%' 
                           AND description NOT LIKE '%TRANSFER%'
                           AND description NOT LIKE '%REFUND%'
                           AND category != 'Payment' THEN 1 END) as suspicious_credits,
                SUM(CASE WHEN is_debit = 0 AND description NOT LIKE '%PAYMENT%' 
                         AND description NOT LIKE '%DEPOSIT%' 
                         AND description NOT LIKE '%TRANSFER%'
                         AND description NOT LIKE '%REFUND%'
                         AND category != 'Payment' THEN amount ELSE 0 END) as suspicious_total
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
        """, (source_id,))
        
        susp_count, susp_total = cursor.fetchone()
        
        if susp_count > 0:
            print(f"\n  🚨 RED FLAG: {susp_count} credits that DON'T look like payments/deposits (${susp_total:,.2f})")
            print(f"     These might be purchases misclassified as credits!")
    
    print(f"\n{'='*120}")
    print(f"TOTALS ACROSS ALL SOURCES")
    print(f"{'='*120}")
    print(f"  Total debits:  ${total_all_debits:,.2f}")
    print(f"  Total credits: ${total_all_credits:,.2f}")
    print(f"  Net spending:  ${total_all_debits - total_all_credits:,.2f}")
    
    # Now calculate what dashboard SHOULD show
    cursor.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
          AND category != 'Payment'
    """)
    
    dashboard_value = cursor.fetchone()[0]
    
    print(f"\n  Dashboard shows: ${dashboard_value:,.2f} (excluding Payment category)")
    print(f"  Still seems high? Let's find why...")
    
    conn.close()


def find_largest_transactions():
    """Show the 20 largest 'debit' transactions in September"""
    print(f"\n{'='*120}")
    print(f"TOP 20 LARGEST TRANSACTIONS IN SEPTEMBER 2025 (marked as debits)")
    print(f"{'='*120}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.transaction_date,
            s.name as source,
            t.description,
            t.amount,
            t.category,
            CASE 
                WHEN t.description LIKE '%PAYMENT%' OR t.description LIKE '%PMT%' THEN '⚠️ Payment?'
                WHEN t.description LIKE '%TRANSFER%' THEN '⚠️ Transfer?'
                WHEN t.description LIKE '%DEPOSIT%' THEN '⚠️ Deposit?'
                ELSE '✓'
            END as flag
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
          AND t.is_debit = 1
        ORDER BY t.amount DESC
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    
    print(f"\n{'Date':<12} {'Source':<20} {'Amount':>12} {'Category':<15} {'Flag':<15} Description")
    print("-" * 120)
    
    for date, source, desc, amt, cat, flag in results:
        print(f"{date:<12} {source:<20} ${amt:>11,.2f} {cat or '?':<15} {flag:<15} {desc[:50]}")
    
    conn.close()


def main():
    print("\n" + "🔍" * 60)
    print(" COMPREHENSIVE DATA ANALYSIS - ALL SOURCES")
    print("🔍" * 60 + "\n")
    
    analyze_all_sources_september()
    find_largest_transactions()
    
    print("\n" + "=" * 120)
    print("LOOK FOR:")
    print("  1. Sources with credits that DON'T look like payments")
    print("  2. Large transactions with ⚠️ flags (might be transfers, not spending)")
    print("  3. Duplicate transactions")
    print("=" * 120 + "\n")


if __name__ == "__main__":
    main()
