#!/usr/bin/env python3
"""
Data Consistency Test for Stop The Monkey
Tests all dashboard calculations against raw database queries
"""
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

DB_PATH = "/home/stopmonkey/monkey/data/stopmonkey.db"

def test_loans():
    """Test loan calculations"""
    print("=" * 60)
    print("TESTING: Loan Calculations")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all active loans
    cursor.execute("""
        SELECT name, loan_type, current_balance 
        FROM loans 
        WHERE is_active = 1
    """)
    loans = cursor.fetchall()
    
    total_debt = 0
    non_mortgage_debt = 0
    
    print(f"\n{'Loan Name':<30} {'Type':<15} {'Balance':>15}")
    print("-" * 60)
    
    for name, loan_type, balance in loans:
        print(f"{name:<30} {loan_type:<15} ${balance:>14,.2f}")
        total_debt += balance
        if loan_type != "mortgage":
            non_mortgage_debt += balance
    
    print("-" * 60)
    print(f"{'TOTAL DEBT:':<45} ${total_debt:>14,.2f}")
    print(f"{'NON-MORTGAGE DEBT:':<45} ${non_mortgage_debt:>14,.2f}")
    
    conn.close()
    return {
        "total_debt": total_debt,
        "non_mortgage_debt": non_mortgage_debt,
        "loan_count": len(loans)
    }


def test_monthly_spending():
    """Test monthly spending calculation"""
    print("\n" + "=" * 60)
    print("TESTING: Monthly Spending Calculation")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = date.today()
    month_start = today.replace(day=1)
    
    print(f"\nCurrent month: {month_start.strftime('%B %Y')}")
    print(f"Date range: {month_start} to {today}")
    
    # Get this month's debits (spending)
    cursor.execute("""
        SELECT 
            COUNT(*) as transaction_count,
            SUM(amount) as total_spent,
            AVG(amount) as avg_transaction
        FROM transactions 
        WHERE transaction_date >= ?
          AND is_debit = 1
          AND (is_excluded = 0 OR is_excluded IS NULL)
    """, (month_start,))
    
    count, total, avg = cursor.fetchone()
    
    print(f"\nTransaction count: {count}")
    print(f"Total spent: ${total:,.2f}")
    print(f"Average per transaction: ${avg:,.2f}")
    
    # Get breakdown by category
    cursor.execute("""
        SELECT 
            category,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions 
        WHERE transaction_date >= ?
          AND is_debit = 1
          AND (is_excluded = 0 OR is_excluded IS NULL)
        GROUP BY category
        ORDER BY total DESC
        LIMIT 10
    """, (month_start,))
    
    categories = cursor.fetchall()
    
    print(f"\n{'Category':<30} {'Count':>8} {'Amount':>15}")
    print("-" * 60)
    for cat, cnt, amt in categories:
        print(f"{cat or '(Uncategorized)':<30} {cnt:>8} ${amt:>14,.2f}")
    
    conn.close()
    return {
        "month_spent": total,
        "transaction_count": count,
        "avg_transaction": avg
    }


def test_spending_trend():
    """Test 6-month spending trend"""
    print("\n" + "=" * 60)
    print("TESTING: 6-Month Spending Trend")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = date.today()
    trend = []
    
    print(f"\n{'Month':<15} {'Transactions':>12} {'Total Spent':>15}")
    print("-" * 60)
    
    for i in range(5, -1, -1):
        m_start = (today - relativedelta(months=i)).replace(day=1)
        m_end = (m_start + relativedelta(months=1)) - relativedelta(days=1)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as count,
                SUM(amount) as total
            FROM transactions 
            WHERE transaction_date >= ?
              AND transaction_date <= ?
              AND is_debit = 1
              AND (is_excluded = 0 OR is_excluded IS NULL)
        """, (m_start, m_end))
        
        count, total = cursor.fetchone()
        month_label = m_start.strftime("%b %Y")
        
        print(f"{month_label:<15} {count:>12} ${total:>14,.2f}")
        
        trend.append({
            "month": month_label,
            "spent": round(float(total or 0), 2),
            "count": count
        })
    
    conn.close()
    return trend


def test_transaction_totals():
    """Verify overall transaction totals"""
    print("\n" + "=" * 60)
    print("TESTING: Overall Transaction Totals")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN is_debit = 1 THEN amount ELSE 0 END) as total_debits,
            SUM(CASE WHEN is_debit = 0 THEN amount ELSE 0 END) as total_credits,
            COUNT(CASE WHEN is_excluded = 1 THEN 1 END) as excluded_count,
            MIN(transaction_date) as earliest_date,
            MAX(transaction_date) as latest_date
        FROM transactions
    """)
    
    total, debits, credits, excluded, earliest, latest = cursor.fetchone()
    net = credits - debits
    
    print(f"\nTotal transactions: {total:,}")
    print(f"Excluded transactions: {excluded:,}")
    print(f"Date range: {earliest} to {latest}")
    print(f"\nTotal debits (spending): ${debits:,.2f}")
    print(f"Total credits (income): ${credits:,.2f}")
    print(f"Net: ${net:,.2f}")
    
    # Check for potential issues
    print("\n" + "⚠️  POTENTIAL ISSUES:" if any([
        debits < 0,
        credits < 0,
        excluded > total * 0.1  # More than 10% excluded
    ]) else "\n✅ No obvious data issues detected")
    
    if debits < 0:
        print("  - Negative total debits (check is_debit flags)")
    if credits < 0:
        print("  - Negative total credits (check is_debit flags)")
    if excluded > total * 0.1:
        print(f"  - High exclusion rate: {excluded/total*100:.1f}% ({excluded}/{total})")
    
    conn.close()
    return {
        "total_transactions": total,
        "total_debits": debits,
        "total_credits": credits,
        "net": net
    }


def find_anomalies():
    """Find potential data anomalies"""
    print("\n" + "=" * 60)
    print("SEARCHING FOR ANOMALIES")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    anomalies = []
    
    # Check for unusually large transactions
    cursor.execute("""
        SELECT transaction_date, description, amount, category
        FROM transactions
        WHERE is_debit = 1 AND amount > 5000
        ORDER BY amount DESC
        LIMIT 10
    """)
    
    large = cursor.fetchall()
    if large:
        print(f"\n⚠️  Large transactions (>$5,000):")
        for date, desc, amt, cat in large:
            print(f"  {date} | ${amt:,.2f} | {desc[:40]} | {cat}")
        anomalies.append(f"{len(large)} transactions over $5,000")
    
    # Check for duplicate transactions
    cursor.execute("""
        SELECT transaction_date, amount, description, COUNT(*) as dup_count
        FROM transactions
        GROUP BY transaction_date, amount, description
        HAVING COUNT(*) > 1
        ORDER BY dup_count DESC
        LIMIT 10
    """)
    
    dupes = cursor.fetchall()
    if dupes:
        print(f"\n⚠️  Potential duplicates:")
        for date, amt, desc, count in dupes:
            print(f"  {date} | ${amt:,.2f} | {desc[:40]} | {count}x")
        anomalies.append(f"{len(dupes)} potential duplicate groups")
    
    # Check for transactions with negative amounts
    cursor.execute("""
        SELECT COUNT(*) FROM transactions WHERE amount < 0
    """)
    neg_count = cursor.fetchone()[0]
    if neg_count > 0:
        print(f"\n⚠️  {neg_count} transactions with negative amounts")
        anomalies.append(f"{neg_count} negative amounts")
    
    # Check for missing categories
    cursor.execute("""
        SELECT COUNT(*) 
        FROM transactions 
        WHERE (category IS NULL OR category = '')
          AND is_debit = 1
    """)
    uncategorized = cursor.fetchone()[0]
    if uncategorized > 0:
        print(f"\n⚠️  {uncategorized} debit transactions without category")
        anomalies.append(f"{uncategorized} uncategorized debits")
    
    if not anomalies:
        print("\n✅ No anomalies detected!")
    
    conn.close()
    return anomalies


def main():
    print("\n" + "🔍" * 30)
    print(" STOP THE MONKEY - DATA CONSISTENCY TEST")
    print("🔍" * 30 + "\n")
    
    try:
        # Run all tests
        loan_results = test_loans()
        spending_results = test_monthly_spending()
        trend_results = test_spending_trend()
        totals_results = test_transaction_totals()
        anomalies = find_anomalies()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"\n✅ Loans analyzed: {loan_results['loan_count']}")
        print(f"✅ Monthly transactions: {spending_results['transaction_count']}")
        print(f"✅ Trend data points: {len(trend_results)}")
        print(f"✅ Total transactions in DB: {totals_results['total_transactions']:,}")
        
        if anomalies:
            print(f"\n⚠️  Anomalies found: {len(anomalies)}")
            for a in anomalies:
                print(f"   - {a}")
        else:
            print("\n✅ No anomalies detected")
        
        print("\n" + "=" * 60)
        print("Next steps:")
        print("  1. Review any anomalies flagged above")
        print("  2. Compare these numbers with dashboard API")
        print("  3. Check specific calculations that seem off")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
