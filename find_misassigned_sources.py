#!/usr/bin/env python3
"""
Find transactions that are likely assigned to the wrong source
Especially: checking account transactions marked as Credit Card 6032
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def find_likely_checking_transactions():
    """Find transactions from 6032 that look like they should be from checking"""
    print("=" * 100)
    print("LIKELY MIS-ASSIGNED TRANSACTIONS (6032 → should be Checking 1569)")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Patterns that indicate checking account, not credit card
    patterns = [
        ('%ELECTRONIC DEPOSIT%', 'Paycheck/deposit'),
        ('%P&G DIST%', 'Paycheck'),
        ('%WEB AUTHORIZED PMT ROBINHOOD%', 'Investment transfer'),
        ('%MOBILE PAYMENT THANK YOU%', 'Payment received'),
        ('%MOBILE BANKING TRANSFER%', 'Transfer'),
        ('%ELECTRONIC WITHDRAWAL%', 'Withdrawal'),
    ]
    
    total_count = 0
    total_amount = 0
    
    for pattern, desc_type in patterns:
        cursor.execute("""
            SELECT COUNT(*), SUM(amount)
            FROM transactions
            WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
              AND description LIKE ?
        """, (pattern,))
        
        count, amount = cursor.fetchone()
        amount = amount or 0
        
        if count > 0:
            print(f"\n{desc_type}:")
            print(f"  Pattern: {pattern}")
            print(f"  Count: {count} transactions")
            print(f"  Total: ${amount:,.2f}")
            
            total_count += count
            total_amount += amount
            
            # Show sample
            cursor.execute("""
                SELECT transaction_date, description, amount
                FROM transactions
                WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
                  AND description LIKE ?
                ORDER BY transaction_date DESC
                LIMIT 3
            """, (pattern,))
            
            samples = cursor.fetchall()
            for date, desc, amt in samples:
                print(f"    {date} | ${amt:>10,.2f} | {desc[:60]}")
    
    print("\n" + "=" * 100)
    print(f"TOTAL LIKELY MIS-ASSIGNED: {total_count} transactions, ${total_amount:,.2f}")
    print("=" * 100)
    
    conn.close()
    return total_count


def find_checking_source_id():
    """Check if Checking 1569 source exists"""
    print("\n" + "=" * 100)
    print("CHECKING ACCOUNT SOURCE STATUS")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, type
        FROM transaction_sources
        WHERE name LIKE '%1569%' OR name LIKE '%Checking%'
    """)
    
    sources = cursor.fetchall()
    
    if sources:
        for source_id, name, stype in sources:
            print(f"\n✅ Found: {name}")
            print(f"   ID: {source_id}")
            print(f"   Type: {stype}")
            
            cursor.execute("""
                SELECT COUNT(*), MIN(transaction_date), MAX(transaction_date)
                FROM transactions
                WHERE source_id = ?
            """, (source_id,))
            
            count, min_date, max_date = cursor.fetchone()
            print(f"   Transactions: {count}")
            print(f"   Date range: {min_date} to {max_date}")
    else:
        print("\n⚠️  No checking account source found!")
        print("   We'll need to create it or use an existing one")
    
    conn.close()


def main():
    print("\n" + "🔍" * 50)
    print(" FINDING MIS-ASSIGNED TRANSACTION SOURCES")
    print("🔍" * 50 + "\n")
    
    count = find_likely_checking_transactions()
    find_checking_source_id()
    
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS:")
    print("=" * 100)
    print("""
1. IMMEDIATE: Create manual source selection in import UI (see IMPORT_FIX_PLAN.md)
2. DATA FIX: Reassign mis-categorized transactions to correct source
3. LONG-TERM: Improve parser detection or require manual selection always

Would you like me to:
A) Create the backend/frontend fix for manual source selection
B) Create a script to reassign the mis-assigned transactions
C) Both
    """)
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
