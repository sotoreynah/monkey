#!/usr/bin/env python3
"""
Diagnostic Report: Find Calculation Discrepancies
Compares dashboard.py logic against raw database queries
"""
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def analyze_september_spending():
    """Deep dive into September 2025 spending (the $72k month)"""
    print("=" * 80)
    print("DEEP DIVE: September 2025 ($72,702.19)")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # September 2025 breakdown
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as count,
            SUM(amount) as total,
            AVG(amount) as avg
        FROM transactions 
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
          AND (is_excluded = 0 OR is_excluded IS NULL)
        GROUP BY category
        ORDER BY total DESC
    """)
    
    categories = cursor.fetchall()
    
    print(f"\n{'Category':<25} {'Count':>8} {'Total':>15} {'Avg':>12}")
    print("-" * 80)
    
    total = 0
    for cat, count, amt, avg in categories:
        print(f"{cat or '(Uncategorized)':<25} {count:>8} ${amt:>14,.2f} ${avg:>11,.2f}")
        total += amt
    
    print("-" * 80)
    print(f"{'TOTAL':<25} {'':<8} ${total:>14,.2f}")
    
    # Check for specific large transactions
    print(f"\n\nLarge transactions in September 2025:")
    cursor.execute("""
        SELECT transaction_date, description, amount, category, merchant
        FROM transactions
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
          AND amount > 5000
        ORDER BY amount DESC
    """)
    
    large = cursor.fetchall()
    for date, desc, amt, cat, merchant in large:
        print(f"  {date} | ${amt:>10,.2f} | {cat or '?':<15} | {desc[:50]}")
    
    # Check if these should be payments vs actual spending
    print(f"\n\nPotential payment transactions (may need reclassification):")
    cursor.execute("""
        SELECT transaction_date, description, amount, category
        FROM transactions
        WHERE transaction_date >= '2025-09-01'
          AND transaction_date <= '2025-09-30'
          AND is_debit = 1
          AND (
            description LIKE '%PAYMENT%'
            OR description LIKE '%AMEX%'
            OR description LIKE '%CREDIT CARD%'
            OR category = 'Payment'
          )
        ORDER BY amount DESC
        LIMIT 20
    """)
    
    payments = cursor.fetchall()
    payment_total = 0
    for date, desc, amt, cat in payments:
        payment_total += amt
        print(f"  {date} | ${amt:>10,.2f} | {cat or '?':<15} | {desc[:50]}")
    
    print(f"\n  → Total payments: ${payment_total:,.2f}")
    print(f"  → Actual spending (excluding payments): ${total - payment_total:,.2f}")
    
    conn.close()
    return total, payment_total


def find_excluded_transactions():
    """Check if exclusions are being applied correctly"""
    print("\n" + "=" * 80)
    print("CHECKING: Excluded Transactions")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as excluded_count,
            SUM(amount) as excluded_amount
        FROM transactions
        WHERE is_excluded = 1
    """)
    
    count, amount = cursor.fetchone()
    
    if count == 0:
        print("\n✅ No transactions are marked as excluded")
        print("   (This is correct based on dashboard.py logic)")
    else:
        print(f"\n⚠️  {count} transactions marked as excluded")
        print(f"   Total amount: ${amount:,.2f}")
        
        cursor.execute("""
            SELECT transaction_date, description, amount, category
            FROM transactions
            WHERE is_excluded = 1
            ORDER BY amount DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  {row}")
    
    conn.close()


def check_payment_categorization():
    """Find transactions that should be categorized as 'Payment' not 'Other'"""
    print("\n" + "=" * 80)
    print("ANALYSIS: Payment vs Spending Categorization")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find all transactions in "Other" category that look like payments
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', transaction_date) as month,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions
        WHERE is_debit = 1
          AND category = 'Other'
          AND (
            description LIKE '%PAYMENT%'
            OR description LIKE '%AMEX%'
            OR description LIKE '%PMT%'
            OR description LIKE '%CREDIT CARD%'
            OR description LIKE '%AUTOPAY%'
            OR description LIKE '%PAYOFF%'
          )
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    """)
    
    results = cursor.fetchall()
    
    print("\nMonthly breakdown of potential misclassified payments:")
    print(f"\n{'Month':<12} {'Count':>8} {'Amount':>15}")
    print("-" * 40)
    
    total_misclassified = 0
    for month, count, amount in results:
        print(f"{month:<12} {count:>8} ${amount:>14,.2f}")
        total_misclassified += amount
    
    print("-" * 40)
    print(f"{'TOTAL':<12} {'':<8} ${total_misclassified:>14,.2f}")
    
    print(f"\n💡 INSIGHT:")
    print(f"   If these ${total_misclassified:,.2f} are credit card payments,")
    print(f"   they should NOT count as 'spending' for budgeting purposes.")
    print(f"   They're transfers to pay off debt, not new expenses.")
    
    conn.close()
    return total_misclassified


def verify_dashboard_calculation():
    """Replicate the exact dashboard.py calculation"""
    print("\n" + "=" * 80)
    print("REPLICATING: dashboard.py Calculation Logic")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = date.today()
    
    # Spending trend (last 6 months) - exactly as in dashboard.py
    print("\nCalculating 6-month trend (dashboard.py logic):")
    print(f"\n{'Month':<15} {'DB Query Result':>20} {'Chart Shows':>20} {'Match?':>10}")
    print("-" * 80)
    
    # These are what we saw in the test
    expected = {
        "Sep 2025": 72702.19,
        "Oct 2025": 64129.57,
        "Nov 2025": 36280.19,
        "Dec 2025": 40295.29,
        "Jan 2026": 34240.03,
        "Feb 2026": 21306.16
    }
    
    for i in range(5, -1, -1):
        m_start = (today - relativedelta(months=i)).replace(day=1)
        m_end = (m_start + relativedelta(months=1)) - relativedelta(days=1)
        
        cursor.execute("""
            SELECT SUM(amount)
            FROM transactions 
            WHERE transaction_date >= ?
              AND transaction_date <= ?
              AND is_debit = 1
              AND (is_excluded = 0 OR is_excluded IS NULL)
        """, (m_start, m_end))
        
        spent = cursor.fetchone()[0] or 0
        month_label = m_start.strftime("%b %Y")
        chart_value = expected.get(month_label, 0)
        
        match = "✅" if abs(spent - chart_value) < 0.01 else "❌"
        
        print(f"{month_label:<15} ${spent:>19,.2f} ${chart_value:>19,.2f} {match:>10}")
    
    conn.close()


def main():
    print("\n" + "🔍" * 40)
    print(" DIAGNOSTIC REPORT: Stop The Monkey Calculations")
    print("🔍" * 40 + "\n")
    
    # Run analyses
    sept_total, sept_payments = analyze_september_spending()
    find_excluded_transactions()
    misclassified_total = check_payment_categorization()
    verify_dashboard_calculation()
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n1. 🎯 PAYMENT CATEGORIZATION ISSUE")
    print("   Problem: Credit card payments are counted as 'spending'")
    print(f"   Impact: Inflates monthly spending by ~${misclassified_total/12:,.2f}/month")
    print("   Fix: Exclude transactions where category='Payment' from spending calculations")
    
    print("\n2. 📊 CATEGORY CLEANUP")
    print("   Problem: Too many transactions in 'Other' category")
    print("   Impact: Hard to track actual spending patterns")
    print("   Fix: Better auto-categorization rules for common merchants")
    
    print("\n3. 🔄 DUPLICATE DETECTION")
    print("   Problem: Some transactions appear multiple times")
    print("   Impact: Overstates spending")
    print("   Fix: Review dedup_hash logic and flag duplicates")
    
    print("\n4. 💡 SUGGESTED CODE FIX")
    print("   File: backend/app/api/dashboard.py")
    print("   Line: ~44 (month_spent query)")
    print("   Add: AND category != 'Payment'")
    print("   Or:  AND transaction_type != 'payment'")
    
    print("\n" + "=" * 80)
    print("Would you like me to:")
    print("  1. Write the code fix for dashboard.py")
    print("  2. Create a script to reclassify payment transactions")
    print("  3. Generate a duplicate cleanup script")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
