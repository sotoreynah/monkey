#!/usr/bin/env python3
"""
Second pass: Recategorize remaining "Other" transactions
"""
import sqlite3

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

# Second-pass categorization rules
RULES = [
    # Transfers & Payments
    ("Transfer", [
        "%RMTLY%",
        "%REMITLY%",
        "%VENMO%",
        "%PAYPAL%",
        "%ZELLE%",
        "%CASHAPP%",
        "%SQ *%",
        "%SQUARE *%",
        "%ROBINHOOD SECURITIES%",
    ]),
    
    # Shopping
    ("Shopping", [
        "%AMAZON MKTPL%",
        "%APPLE%STORE%",
        "%APPLE.COM/US%",
        "%TSPORTLINE%",
        "%FUTUREMOTION%",
    ]),
    
    # Travel
    ("Transportation", [
        "%AIRBNB%",
    ]),
    
    # Personal Care
    ("Services", [
        "%HENRI%CLOUD NINE%",
        "%SALON%",
        "%BARBER%",
    ]),
]


def preview_and_apply():
    """Preview and apply second-pass recategorization"""
    print("\n" + "🔧" * 50)
    print(" SECOND-PASS RECATEGORIZATION")
    print("🔧" * 50 + "\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_updated = 0
    
    for new_category, patterns in RULES:
        for pattern in patterns:
            # Check how many will be affected
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM transactions
                WHERE category = 'Other'
                  AND description LIKE ?
            """, (pattern,))
            
            count, amount = cursor.fetchone()
            
            if count > 0:
                # Apply update
                cursor.execute("""
                    UPDATE transactions
                    SET category = ?
                    WHERE category = 'Other'
                      AND description LIKE ?
                """, (new_category, pattern))
                
                print(f"✅ {new_category}: {count} transactions (${amount:,.2f}) - {pattern}")
                total_updated += count
    
    conn.commit()
    
    # Final stats
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE category = 'Other'
    """)
    
    remaining, remaining_amount = cursor.fetchone()
    
    print("\n" + "=" * 80)
    print(f"✅ Second pass complete: {total_updated} transactions recategorized")
    print(f"📊 Remaining 'Other': {remaining} transactions (${remaining_amount:,.2f})")
    print("=" * 80 + "\n")
    
    conn.close()


if __name__ == "__main__":
    preview_and_apply()
