#!/usr/bin/env python3
"""
Investigate Apple Card sign inversion issue
Focus on September 2025 to understand the problem
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def analyze_sources():
    """Show all transaction sources and their behavior"""
    print("=" * 80)
    print("TRANSACTION SOURCES")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, type, institution, last_four
        FROM transaction_sources
        ORDER BY name
    """)
    
    sources = cursor.fetchall()
    
    print(f"\n{'ID':<5} {'Name':<30} {'Type':<15} {'Institution':<20} {'Last 4':<10}")
    print("-" * 80)
    for source_id, name, src_type, inst, last_four in sources:
        print(f"{source_id:<5} {name:<30} {src_type or '?':<15} {inst or '?':<20} {last_four or '?':<10}")
    
    conn.close()
    return sources


def analyze_september_by_source():
    """Break down September 2025 by source to find the culprit"""
    print("\n" + "=" * 80)
    print("SEPTEMBER 2025 BREAKDOWN BY SOURCE")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get spending by source (excluding Payment category)
    cursor.execute("""
        SELECT 
            s.name as source_name,
            s.type as source_type,
            COUNT(*) as transaction_count,
            SUM(CASE WHEN t.is_debit = 1 THEN t.amount ELSE 0 END) as total_debits,
            SUM(CASE WHEN t.is_debit = 0 THEN t.amount ELSE 0 END) as total_credits,
            AVG(t.amount) as avg_amount
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
          AND t.category != 'Payment'
        GROUP BY s.name, s.type
        ORDER BY total_debits DESC
    """)
    
    results = cursor.fetchall()
    
    print(f"\n{'Source':<25} {'Type':<12} {'Count':>7} {'Debits':>15} {'Credits':>15} {'Avg':>12}")
    print("-" * 95)
    
    total_debits = 0
    total_credits = 0
    
    for source, stype, count, debits, credits, avg in results:
        print(f"{source:<25} {stype or '?':<12} {count:>7} ${debits:>14,.2f} ${credits:>14,.2f} ${avg:>11,.2f}")
        total_debits += debits
        total_credits += credits
    
    print("-" * 95)
    print(f"{'TOTALS':<25} {'':<12} {'':<7} ${total_debits:>14,.2f} ${credits:>14,.2f}")
    
    conn.close()


def check_apple_card_signs():
    """Look at Apple Card transactions specifically to see sign pattern"""
    print("\n" + "=" * 80)
    print("APPLE CARD TRANSACTION SIGN ANALYSIS")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get Apple Card source ID
    cursor.execute("SELECT id, name FROM transaction_sources WHERE name LIKE '%Apple%' OR institution LIKE '%Apple%'")
    apple_sources = cursor.fetchall()
    
    if not apple_sources:
        print("\n⚠️  No Apple Card source found!")
        conn.close()
        return
    
    for source_id, source_name in apple_sources:
        print(f"\n📱 Source: {source_name} (ID: {source_id})")
        print("-" * 80)
        
        # Sample transactions to see the pattern
        cursor.execute("""
            SELECT 
                transaction_date,
                description,
                amount,
                is_debit,
                category,
                transaction_type
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
            ORDER BY amount DESC
            LIMIT 20
        """, (source_id,))
        
        txns = cursor.fetchall()
        
        print(f"\n{'Date':<12} {'Description':<35} {'Amount':>12} {'Debit?':>7} {'Category':<15} {'Type':<10}")
        print("-" * 100)
        
        for date, desc, amt, is_debit, cat, txn_type in txns:
            debit_flag = "✓" if is_debit else "✗"
            print(f"{date:<12} {desc[:35]:<35} ${amt:>11,.2f} {debit_flag:>7} {cat or '?':<15} {txn_type or '?':<10}")
        
        # Check for sign inversion pattern
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN is_debit = 1 AND amount < 0 THEN 1 END) as negative_debits,
                COUNT(CASE WHEN is_debit = 0 AND amount < 0 THEN 1 END) as negative_credits,
                COUNT(CASE WHEN is_debit = 1 AND amount > 0 THEN 1 END) as positive_debits,
                COUNT(CASE WHEN is_debit = 0 AND amount > 0 THEN 1 END) as positive_credits
            FROM transactions
            WHERE source_id = ?
              AND transaction_date >= '2025-09-01'
              AND transaction_date <= '2025-09-30'
        """, (source_id,))
        
        neg_deb, neg_cred, pos_deb, pos_cred = cursor.fetchone()
        
        print(f"\n📊 Sign Analysis for {source_name}:")
        print(f"   Positive amount + is_debit=1: {pos_deb}")
        print(f"   Positive amount + is_debit=0: {pos_cred}")
        print(f"   Negative amount + is_debit=1: {neg_deb}")
        print(f"   Negative amount + is_debit=0: {neg_cred}")
        
        if neg_deb > 0 or pos_cred > 0:
            print("\n   ⚠️  POTENTIAL SIGN INVERSION DETECTED!")
            print("   Expected: Debits should be positive, Credits should be negative (or vice versa)")
    
    conn.close()


def compare_apple_vs_others():
    """Compare Apple Card behavior vs other sources"""
    print("\n" + "=" * 80)
    print("APPLE CARD VS OTHER SOURCES - SIGN PATTERN")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Apple Card
    cursor.execute("""
        SELECT 
            'Apple Card' as source,
            COUNT(*) as total,
            SUM(CASE WHEN is_debit = 1 AND amount > 0 THEN 1 ELSE 0 END) as pos_debit,
            SUM(CASE WHEN is_debit = 0 AND amount > 0 THEN 1 ELSE 0 END) as pos_credit,
            SUM(CASE WHEN is_debit = 1 AND amount < 0 THEN 1 ELSE 0 END) as neg_debit,
            SUM(CASE WHEN is_debit = 0 AND amount < 0 THEN 1 ELSE 0 END) as neg_credit
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE (s.name LIKE '%Apple%' OR s.institution LIKE '%Apple%')
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
    """)
    
    apple_stats = cursor.fetchone()
    
    # Other sources
    cursor.execute("""
        SELECT 
            'Other Sources' as source,
            COUNT(*) as total,
            SUM(CASE WHEN is_debit = 1 AND amount > 0 THEN 1 ELSE 0 END) as pos_debit,
            SUM(CASE WHEN is_debit = 0 AND amount > 0 THEN 1 ELSE 0 END) as pos_credit,
            SUM(CASE WHEN is_debit = 1 AND amount < 0 THEN 1 ELSE 0 END) as neg_debit,
            SUM(CASE WHEN is_debit = 0 AND amount < 0 THEN 1 ELSE 0 END) as neg_credit
        FROM transactions t
        JOIN transaction_sources s ON t.source_id = s.id
        WHERE s.name NOT LIKE '%Apple%' AND (s.institution NOT LIKE '%Apple%' OR s.institution IS NULL)
          AND t.transaction_date >= '2025-09-01'
          AND t.transaction_date <= '2025-09-30'
    """)
    
    other_stats = cursor.fetchone()
    
    print(f"\n{'Source':<20} {'Total':>8} {'+Debit':>10} {'+Credit':>10} {'-Debit':>10} {'-Credit':>10}")
    print("-" * 80)
    
    for stats in [apple_stats, other_stats]:
        if stats:
            source, total, pos_deb, pos_cred, neg_deb, neg_cred = stats
            print(f"{source:<20} {total:>8} {pos_deb:>10} {pos_cred:>10} {neg_deb:>10} {neg_cred:>10}")
    
    print("\n💡 PATTERN TO LOOK FOR:")
    print("   If Apple Card has opposite pattern from others, that's the bug!")
    print("   Example: Others have +Debit, Apple has -Debit (or vice versa)")
    
    conn.close()


def main():
    print("\n" + "🔍" * 40)
    print(" APPLE CARD SIGN INVESTIGATION - September 2025")
    print("🔍" * 40 + "\n")
    
    sources = analyze_sources()
    analyze_september_by_source()
    check_apple_card_signs()
    compare_apple_vs_others()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("\n1. Review the sign patterns above")
    print("2. Identify which source has inverted logic")
    print("3. Create a fix script to flip is_debit flag for affected transactions")
    print("4. Re-test September numbers after fix")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
