#!/usr/bin/env python3
"""
Recategorize "Other" transactions based on merchant patterns
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

# Categorization rules (order matters - most specific first)
RULES = [
    # Income & Credits
    ("Income", [
        "%ELECTRONIC DEPOSIT P&G%",
        "%ELECTRONIC DEPOSIT%IRS%",
        "%ELECTRONIC DEPOSIT%ROBINHOOD%",
        "%ELECTRONIC DEPOSIT%LIGHTSTREAM%",
        "%ELECTRONIC DEPOSIT%",
        "%MOBILE CHECK DEPOSIT%",
        "%PAYCHECK%",
        "%DIRECT DEPOSIT%",
    ]),
    ("Payment Received", [
        "%MOBILE PAYMENT%THANK YOU%",
        "%MOBILE PAYMENT - THANK YOU%",
        "%INTERNET PAYMENT THANK YOU%",
    ]),
    
    # Loan Payments (Debits)
    ("Payment", [
        "%ELECTRONIC WITHDRAWAL%HEARTLAND%",
        "%ELECTRONIC WITHDRAWAL%GERMAN AMER%",
        "%ELECTRONIC WITHDRAWAL%SANTANDER%",
        "%ELECTRONIC WITHDRAWAL%TESLA MOTORS%",
        "%ELECTRONIC WITHDRAWAL%VW CREDIT%",
        "%ELECTRONIC WITHDRAWAL%LIGHTSTREAM%",
    ]),
    
    # Subscriptions & Services
    ("Services", [
        "%APPLE.COM/BILL%",
        "%LIFE TIME%#376%",
        "%KHAN ACADEMY%",
        "%PRIME VIDEO%",
        "%NETFLIX%",
        "%SPOTIFY%",
        "%YOUTUBE%",
        "%AMAZON PRIME%",
    ]),
    
    # Utilities
    ("Utilities", [
        "%altafiber%",
        "%DUKE ENERGY%",
        "%CINCINNATI BELL%",
        "%SPECTRUM%",
        "%AT&T%",
        "%VERIZON%",
    ]),
    
    # Transportation
    ("Transportation", [
        "%TESLA SUPERCHARGER%",
        "%DELTA AIR%",
        "%AMERICAN AIRLINES%",
        "%UNITED AIRLINES%",
        "%UBER%",
        "%LYFT%",
    ]),
    
    # Groceries
    ("Groceries", [
        "%WHOLEFDS%",
        "%WHOLE FOODS%",
    ]),
    
    # Shopping
    ("Shopping", [
        "%CHARMIN%P&G%",
        "%CRUTCHFIELD%",
        "%AMAZON.COM%",
        "%TARGET%",
        "%WALMART%",
    ]),
    
    # Entertainment
    ("Entertainment", [
        "%TM *BRUNO MARS%",
        "%TICKETMASTER%",
    ]),
    
    # Cash & Transfers
    ("Cash", [
        "%ATM WITHDRAWAL%",
        "%ATM DEPOSIT%",
    ]),
    ("Transfer", [
        "%APPLE CASH SENT%",
        "%WIRE TRANSFER%",
        "%MOBILE BANKING TRANSFER%",
        "%CHECK%",
        "%DEPOSIT%",
    ]),
    
    # Fees
    ("Interest/Fees", [
        "%MONTHLY MAINTENANCE FEE%",
        "%OVERDRAFT%",
        "%LATE FEE%",
        "%ANNUAL FEE%",
    ]),
    
    # Credits/Refunds
    ("Other", [
        "%FEE WAIVED%",
        "%REVERSED%FEE%",
        "%REFUND%",
        "%REVERSAL%",
    ]),
]


def preview_recategorization():
    """Show what will be recategorized"""
    print("=" * 100)
    print("PREVIEW: Recategorization of 'Other' Transactions")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_moved = 0
    changes = {}
    
    for new_category, patterns in RULES:
        for pattern in patterns:
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM transactions
                WHERE category = 'Other'
                  AND description LIKE ?
            """, (pattern,))
            
            count, amount = cursor.fetchone()
            
            if count > 0:
                if new_category not in changes:
                    changes[new_category] = {"count": 0, "amount": 0, "patterns": []}
                changes[new_category]["count"] += count
                changes[new_category]["amount"] += amount
                changes[new_category]["patterns"].append(f"{pattern} ({count} txns)")
                total_moved += count
    
    # Display summary
    for category, data in sorted(changes.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"\n{category}:")
        print(f"  Transactions: {data['count']}")
        print(f"  Total amount: ${data['amount']:,.2f}")
        print(f"  Patterns:")
        for p in data['patterns']:
            print(f"    - {p}")
    
    # What remains
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE category = 'Other'
    """)
    total_other, total_amount = cursor.fetchone()
    
    remaining = total_other - total_moved
    
    print("\n" + "=" * 100)
    print(f"SUMMARY:")
    print(f"  Current 'Other': {total_other} transactions (${total_amount:,.2f})")
    print(f"  Will recategorize: {total_moved} transactions")
    print(f"  Remaining 'Other': {remaining} transactions")
    print(f"  Improvement: {(total_moved / total_other * 100):.1f}% reduction")
    print("=" * 100)
    
    conn.close()
    return total_moved


def apply_recategorization():
    """Execute the recategorization"""
    print("\n" + "=" * 100)
    print("APPLYING RECATEGORIZATION")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_updated = 0
    
    for new_category, patterns in RULES:
        for pattern in patterns:
            sql = """
                UPDATE transactions
                SET category = ?
                WHERE category = 'Other'
                  AND description LIKE ?
            """
            
            cursor.execute(sql, (new_category, pattern))
            updated = cursor.rowcount
            
            if updated > 0:
                print(f"✅ {new_category}: {updated} transactions ({pattern})")
                total_updated += updated
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total recategorized: {total_updated} transactions")
    
    return total_updated


def verify_recategorization():
    """Verify the recategorization worked"""
    print("\n" + "=" * 100)
    print("VERIFICATION")
    print("=" * 100)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Category distribution after fix
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM transactions), 1) as percentage,
            ROUND(SUM(amount), 2) as total_amount
        FROM transactions
        GROUP BY category
        ORDER BY count DESC
        LIMIT 15
    """)
    
    print("\nCategory Distribution (After):")
    print(f"{'Category':<20} {'Count':>8} {'Percentage':>12} {'Total Amount':>15}")
    print("-" * 60)
    
    for row in cursor.fetchall():
        category, count, pct, amount = row
        print(f"{category:<20} {count:>8} {pct:>11}% ${amount:>13,.2f}")
    
    # Sample remaining "Other"
    cursor.execute("""
        SELECT description, amount, is_debit
        FROM transactions
        WHERE category = 'Other'
        ORDER BY amount DESC
        LIMIT 10
    """)
    
    print("\n\nRemaining 'Other' (Top 10):")
    print(f"{'Description':<60} {'Amount':>12} {'Type':>8}")
    print("-" * 82)
    
    for desc, amt, is_debit in cursor.fetchall():
        txn_type = "Debit" if is_debit else "Credit"
        print(f"{desc[:60]:<60} ${amt:>10,.2f} {txn_type:>8}")
    
    conn.close()


def main():
    print("\n" + "🔄" * 50)
    print(" RECATEGORIZE 'OTHER' TRANSACTIONS")
    print("🔄" * 50 + "\n")
    
    # Show preview
    moved = preview_recategorization()
    
    if moved == 0:
        print("\n✅ No transactions need recategorization!")
        return
    
    # Confirm
    print(f"\n⚠️  Ready to recategorize {moved} transactions")
    response = input("\nProceed? (yes/no): ")
    
    if response.lower() == 'yes':
        updated = apply_recategorization()
        verify_recategorization()
        
        print("\n" + "=" * 100)
        print("NEXT STEPS:")
        print("  1. ✅ Recategorization complete")
        print("  2. Restart backend to refresh cache")
        print("  3. Refresh dashboard - categories should be more accurate")
        print("  4. Update parser logic to prevent future mis-categorization")
        print("=" * 100 + "\n")
    else:
        print("\n❌ Recategorization cancelled")


if __name__ == "__main__":
    main()
