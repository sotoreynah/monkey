import pandas as pd
from typing import List, Dict
from app.parsers.base_parser import BaseParser


class CreditCard6032Parser(BaseParser):
    SOURCE_NAME = "Credit Card 6032"
    SOURCE_TYPE = "credit_card"
    EXPECTED_COLUMNS = {"Date", "Transaction", "Name", "Memo", "Amount"}

    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        transactions = []
        for _, row in df.iterrows():
            trans_type = str(row.get("Transaction", "")).strip().upper()
            is_debit = trans_type == "DEBIT"
            name = str(row.get("Name", "")).strip()
            amount = float(row.get("Amount", 0))
            date_str = str(row.get("Date", "")).strip()
            memo = str(row.get("Memo", "")).strip() if pd.notna(row.get("Memo")) else None

            category = self._categorize(name)

            transactions.append({
                "transaction_date": pd.to_datetime(date_str).date(),
                "description": name,
                "merchant": self._extract_merchant(name),
                "category": category,
                "original_category": None,
                "transaction_type": trans_type.lower(),
                "amount": abs(amount),
                "is_debit": is_debit,
                "memo": memo,
                "dedup_hash": self.make_dedup_hash(self.SOURCE_NAME, date_str, str(amount), name),
            })
        return transactions

    def _extract_merchant(self, name: str) -> str:
        prefixes = ["DEBIT PURCHASE -VISA ", "CREDIT -"]
        for p in prefixes:
            if name.upper().startswith(p):
                name = name[len(p):].strip()
        return name.split("  ")[0].strip()[:80]

    def _categorize(self, name: str) -> str:
        n = name.upper()
        if any(k in n for k in ["KROGER", "WHOLE FOODS", "COSTCO", "FRESH MARKET", "TRADER JOE"]):
            return "Groceries"
        if "INTEREST CHARGE" in n:
            return "Interest/Fees"
        if "CASH ADVANCE" in n:
            return "Interest/Fees"
        if any(k in n for k in ["RESTAURANT", "CAFE", "PIZZA", "TACO", "SUSHI", "GRILLE", "GRILL"]):
            return "Dining"
        if any(k in n for k in ["PARKING", "GARAGE"]):
            return "Transportation"
        if any(k in n for k in ["PAYMENT TO CREDIT", "MOBILE BANKING"]):
            return "Payment"
        return "Other"
