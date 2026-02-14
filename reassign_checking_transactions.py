#!/usr/bin/env python3
"""
Reassign transactions from Credit Card 6032 to Checking 1569
ONLY for transactions that clearly belong to checking account
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def preview_reassignment():
    """Show what will be reassigned"""
    print("=" * 100)
    print("PREVIEW: Transactions to Reassign from Credit Card 6032 → Checking 1569")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define patterns that CLEARLY indicate checking account
    patterns = [
        ('%ELECTRONIC DEPOSIT%', 'Paycheck/Income deposits'),
        ('%P&G DIST%', 'P&G paycheck'),
        ('%ELECTRONIC WITHDRAWAL HEARTLAND%', 'Mortgage payment'),
        ('%ELECTRONIC WITHDRAWAL SANTANDER%', 'Auto loan payment'),
        ('%ELECTRONIC WITHDRAWAL GERMAN AMER%', 'Auto loan payment'),
        ('%ELECTRONIC WITHDRAWAL TESLA%', 'Auto loan payment'),
        ('%ELECTRONIC WITHDRAWAL VW CREDIT%', 'Auto loan payment'),
        ('%ELECTRONIC WITHDRAWAL LIGHTSTREAM%', 'Personal loan payment'),
        ('%MOBILE BANKING TRANSFER%', 'Account transfers'),
        ('%MOBILE PAYMENT THANK YOU%', 'Payments received'),
        ('%WIRE TRANSFER%', 'Wire transfers'),
        # WEB AUTHORIZED PMT are bill payments FROM checking account
        # But we already fixed their category, so they stay in 6032 with category=Payment
    ]
    
    total_count = 0
    total_amount = 0
    
    all_ids = []
    
    for pattern, description in patterns:
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0), GROUP_CONCAT(id)
            FROM transactions
            WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
              AND description LIKE ?
        """, (pattern,))
        
        count, amount, ids = cursor.fetchone()
        
        if count > 0:
            print(f"\n{description}:")
            print(f"  Pattern: {pattern}")
            print(f"  Count: {count} transactions")
            print(f"  Total: ${amount:,.2f}")
            
            total_count += count
            total_amount += amount
            
            if ids:
                all_ids.extend(ids.split(','))
            
            # Show sample
            cursor.execute("""
                SELECT id, transaction_date, description, amount
                FROM transactions
                WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
                  AND description LIKE ?
                ORDER BY transaction_date DESC
                LIMIT 2
            """, (pattern,))
            
            samples = cursor.fetchall()
            for txn_id, date, desc, amt in samples:
                print(f"    ID {txn_id:>6} | {date} | ${amt:>10,.2f} | {desc[:50]}")
    
    print("\n" + "=" * 100)
    print(f"TOTAL TO REASSIGN: {total_count} transactions, ${total_amount:,.2f}")
    print("=" * 100)
    
    conn.close()
    return all_ids, total_count, total_amount


def apply_reassignment():
    """Execute the reassignment"""
    print("\n" + "=" * 100)
    print("APPLYING REASSIGNMENT")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get source IDs
    cursor.execute("SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032'")
    source_6032 = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM transaction_sources WHERE name = 'Checking'")
    source_checking = cursor.fetchone()
    
    if not source_checking:
        print("\n⚠️  'Checking' source not found. Creating it...")
        cursor.execute("""
            INSERT INTO transaction_sources (name, type, institution, active)
            VALUES ('Checking', 'checking', 'Checking 1569', 1)
        """)
        conn.commit()
        cursor.execute("SELECT id FROM transaction_sources WHERE name = 'Checking'")
        source_checking = cursor.fetchone()[0]
        print(f"✅ Created Checking source with ID: {source_checking}")
    else:
        source_checking = source_checking[0]
        print(f"✅ Found Checking source with ID: {source_checking}")
    
    # Patterns for reassignment
    patterns = [
        '%ELECTRONIC DEPOSIT%',
        '%P&G DIST%',
        '%ELECTRONIC WITHDRAWAL HEARTLAND%',
        '%ELECTRONIC WITHDRAWAL SANTANDER%',
        '%ELECTRONIC WITHDRAWAL GERMAN AMER%',
        '%ELECTRONIC WITHDRAWAL TESLA%',
        '%ELECTRONIC WITHDRAWAL VW CREDIT%',
        '%ELECTRONIC WITHDRAWAL LIGHTSTREAM%',
        '%MOBILE BANKING TRANSFER%',
        '%MOBILE PAYMENT THANK YOU%',
        '%WIRE TRANSFER%',
    ]
    
    # Build WHERE clause
    conditions = ' OR '.join([f"description LIKE ?" for _ in patterns])
    
    # Update transactions
    sql = f"""
        UPDATE transactions
        SET source_id = ?
        WHERE source_id = ?
          AND ({conditions})
    """
    
    params = [source_checking, source_6032] + patterns
    
    cursor.execute(sql, params)
    updated_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Reassigned {updated_count} transactions")
    print(f"   From: Credit Card 6032 (ID {source_6032})")
    print(f"   To: Checking (ID {source_checking})")
    
    return updated_count


def verify_reassignment():
    """Verify the reassignment worked"""
    print("\n" + "=" * 100)
    print("VERIFICATION")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Credit Card 6032 remaining transactions
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
    """)
    
    remaining_count, remaining_amount = cursor.fetchone()
    
    print(f"\nCredit Card 6032 (remaining):")
    print(f"  Transactions: {remaining_count}")
    print(f"  Total amount: ${remaining_amount:,.2f}")
    
    # Check Checking account
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Checking')
    """)
    
    checking_count, checking_amount = cursor.fetchone()
    
    print(f"\nChecking (after reassignment):")
    print(f"  Transactions: {checking_count}")
    print(f"  Total amount: ${checking_amount:,.2f}")
    
    # Sample transactions from each
    print(f"\nSample from Credit Card 6032 (should be actual credit card purchases):")
    cursor.execute("""
        SELECT transaction_date, description, amount
        FROM transactions
        WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Credit Card 6032')
        ORDER BY transaction_date DESC
        LIMIT 3
    """)
    
    for date, desc, amt in cursor.fetchall():
        print(f"  {date} | ${amt:>10,.2f} | {desc[:60]}")
    
    print(f"\nSample from Checking (should be deposits/withdrawals/transfers):")
    cursor.execute("""
        SELECT transaction_date, description, amount
        FROM transactions
        WHERE source_id = (SELECT id FROM transaction_sources WHERE name = 'Checking')
        ORDER BY transaction_date DESC
        LIMIT 3
    """)
    
    for date, desc, amt in cursor.fetchall():
        print(f"  {date} | ${amt:>10,.2f} | {desc[:60]}")
    
    conn.close()


def main():
    print("\n" + "🔧" * 50)
    print(" REASSIGN CHECKING ACCOUNT TRANSACTIONS")
    print("🔧" * 50 + "\n")
    
    # Show preview
    ids, count, amount = preview_reassignment()
    
    if count == 0:
        print("\n✅ No transactions need reassignment!")
        return
    
    # Confirm
    print("\n⚠️  Ready to reassign these transactions from Credit Card 6032 → Checking")
    print(f"   This will affect {count} transactions totaling ${amount:,.2f}")
    response = input("\nProceed? (yes/no): ")
    
    if response.lower() == 'yes':
        updated = apply_reassignment()
        verify_reassignment()
        
        print("\n" + "=" * 100)
        print("NEXT STEPS:")
        print("  1. ✅ Data reassignment complete")
        print("  2. Restart backend to ensure clean state")
        print("  3. Refresh dashboard - numbers should be more accurate")
        print("  4. Implement manual source selection to prevent this in future uploads")
        print("=" * 100 + "\n")
    else:
        print("\n❌ Reassignment cancelled")


if __name__ == "__main__":
    main()
