import pandas as pd
from typing import List, Dict
from app.parsers.base_parser import BaseParser


class AppleCardParser(BaseParser):
    SOURCE_NAME = "Apple Card"
    SOURCE_TYPE = "credit_card"
    EXPECTED_COLUMNS = {
        "Transaction Date", "Clearing Date", "Description",
        "Merchant", "Category", "Type", "Amount (USD)", "Purchased By"
    }

    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        transactions = []
        for _, row in df.iterrows():
            txn_type = str(row.get("Type", "")).strip().lower()
            is_debit = txn_type in ("purchase", "debit")
            amount = float(row.get("Amount (USD)", 0))
            date_str = str(row.get("Transaction Date", "")).strip()
            clearing_str = str(row.get("Clearing Date", "")).strip()
            description = str(row.get("Description", "")).strip()
            merchant = str(row.get("Merchant", "")).strip() if pd.notna(row.get("Merchant")) else description
            category = str(row.get("Category", "")).strip() if pd.notna(row.get("Category")) else None
            purchased_by = str(row.get("Purchased By", "")).strip() if pd.notna(row.get("Purchased By")) else None

            # Normalize category
            normalized_cat = self._normalize_category(category) if category else "Other"

            transactions.append({
                "transaction_date": pd.to_datetime(date_str).date(),
                "clearing_date": pd.to_datetime(clearing_str).date() if clearing_str and clearing_str != "nan" else None,
                "description": description,
                "merchant": merchant[:80],
                "category": normalized_cat,
                "original_category": category,
                "transaction_type": txn_type,
                "amount": abs(amount),
                "is_debit": is_debit,
                "purchased_by": purchased_by,
                "dedup_hash": self.make_dedup_hash(self.SOURCE_NAME, date_str, str(amount), description),
            })
        return transactions

    def _normalize_category(self, cat: str) -> str:
        mapping = {
            "Restaurants": "Dining",
            "Grocery": "Groceries",
            "Food & Drink": "Dining",
            "Shopping": "Shopping",
            "Entertainment": "Entertainment",
            "Health": "Health",
            "Transportation": "Transportation",
            "Utilities": "Utilities",
            "Insurance": "Insurance",
            "Credit": "Payment",
            "Other": "Other",
        }
        return mapping.get(cat, cat or "Other")
