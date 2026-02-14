#!/usr/bin/env python3
"""
Analyze the uploaded CSV files to determine correct source assignment
"""
import pandas as pd
import os

CSV_DIR = "/root/.clawdbot/media/inbound/"

def analyze_csv(file_path):
    """Analyze a single CSV file"""
    filename = os.path.basename(file_path)
    print(f"\n{'='*100}")
    print(f"FILE: {filename}")
    print(f"{'='*100}")
    
    # Read first few rows
    df = pd.read_csv(file_path, nrows=10)
    
    # Show columns
    print(f"\nColumns: {list(df.columns)}")
    
    # Determine which parser would match
    columns = set(c.strip() for c in df.columns)
    
    print(f"\nColumn set: {columns}")
    
    # Check against parser expected columns
    checking_cols = {"Date", "Transaction", "Name", "Memo", "Amount"}
    credit_6032_cols = {"Date", "Transaction", "Name", "Memo", "Amount"}
    apple_cols = {"Transaction Date", "Clearing Date", "Description", "Merchant", "Category", "Type", "Amount (USD)", "Purchased By"}
    amex_cols = {"Date", "Description", "Card Member", "Account #", "Amount", "Extended Details"}
    
    matched_parser = None
    if checking_cols.issubset(columns):
        matched_parser = "Checking 1569 OR Credit Card 6032 (AMBIGUOUS!)"
    if apple_cols.issubset(columns):
        matched_parser = "Apple Card"
    if amex_cols.issubset(columns):
        matched_parser = "AMEX"
    
    print(f"\nAuto-detected parser: {matched_parser}")
    
    # Show sample transactions
    print(f"\nSample transactions:")
    for i, row in df.head(5).iterrows():
        if 'Name' in df.columns:
            name = str(row.get('Name', ''))[:60]
            amount = row.get('Amount', 0)
            trans = row.get('Transaction', '')
            print(f"  {trans:<15} | ${amount:>10} | {name}")
        elif 'Description' in df.columns:
            desc = str(row.get('Description', ''))[:60]
            amount = row.get('Amount', row.get('Amount (USD)', 0))
            print(f"  ${amount:>10} | {desc}")
    
    # Analyze content to determine REAL source
    print(f"\nContent analysis:")
    if 'Name' in df.columns:
        sample_names = df['Name'].head(10).tolist()
        
        # Check for checking account indicators
        checking_indicators = [
            'ELECTRONIC DEPOSIT',
            'P&G DIST',
            'MOBILE BANKING TRANSFER',
            'MOBILE PAYMENT THANK YOU',
            'ELECTRONIC WITHDRAWAL',
        ]
        
        credit_indicators = [
            'DEBIT PURCHASE -VISA',
            'CREDIT -',
        ]
        
        checking_matches = sum(1 for name in sample_names if any(ind in str(name) for ind in checking_indicators))
        credit_matches = sum(1 for name in sample_names if any(ind in str(name) for ind in credit_indicators))
        
        print(f"  Checking account indicators: {checking_matches}")
        print(f"  Credit card indicators: {credit_matches}")
        
        if checking_matches > 0:
            print(f"  ✅ LIKELY SOURCE: Checking 1569")
            return "Checking 1569"
        elif credit_matches > 0:
            print(f"  ✅ LIKELY SOURCE: Credit Card 6032")
            return "Credit Card 6032"
        else:
            print(f"  ⚠️  AMBIGUOUS - need manual selection")
            return "UNKNOWN"
    
    elif 'Transaction Date' in df.columns and 'Purchased By' in df.columns:
        print(f"  ✅ DEFINITE SOURCE: Apple Card")
        return "Apple Card"
    
    elif 'Card Member' in df.columns:
        print(f"  ✅ DEFINITE SOURCE: AMEX")
        return "AMEX"
    
    return "UNKNOWN"


def main():
    print("\n" + "🔍" * 50)
    print(" ANALYZING UPLOADED CSV FILES")
    print("🔍" * 50)
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    results = {}
    for csv_file in sorted(csv_files):
        file_path = os.path.join(CSV_DIR, csv_file)
        source = analyze_csv(file_path)
        results[csv_file] = source
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    for filename, source in results.items():
        print(f"\n{filename}")
        print(f"  → {source}")
    
    print("\n" + "=" * 100)
    print("CONCLUSION:")
    print("=" * 100)
    print("""
The auto-detection IS broken for files with identical column structure.
Files with "Date,Transaction,Name,Memo,Amount" could be EITHER:
  - Checking 1569 (if contains ELECTRONIC DEPOSIT, P&G, etc.)
  - Credit Card 6032 (if contains DEBIT PURCHASE -VISA, etc.)

Without manual source selection, all get assigned to whichever parser is checked first!

RECOMMENDATION: Implement manual source selection BEFORE importing more data.
    """)
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
