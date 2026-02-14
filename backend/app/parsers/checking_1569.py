import pandas as pd
from typing import List, Dict
from app.parsers.base_parser import BaseParser


class Checking1569Parser(BaseParser):
    SOURCE_NAME = "Checking 1569"
    SOURCE_TYPE = "checking"
    EXPECTED_COLUMNS = {"Date", "Transaction", "Name", "Memo", "Amount"}

    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        transactions = []
        for _, row in df.iterrows():
            trans_type = str(row.get("Transaction", "")).strip()
            name = str(row.get("Name", "")).strip()
            amount = float(row.get("Amount", 0))
            date_str = str(row.get("Date", "")).strip()
            memo = str(row.get("Memo", "")).strip() if pd.notna(row.get("Memo")) else None

            # In checking: negative = money out, positive = money in
            is_debit = amount < 0
            category = self._categorize(name, trans_type)

            transactions.append({
                "transaction_date": pd.to_datetime(date_str).date(),
                "description": name,
                "merchant": self._extract_merchant(name),
                "category": category,
                "original_category": None,
                "transaction_type": trans_type.lower().replace(" ", "_"),
                "amount": abs(amount),
                "is_debit": is_debit,
                "memo": memo,
                "dedup_hash": self.make_dedup_hash(self.SOURCE_NAME, date_str, str(amount), name),
            })
        return transactions

    def _extract_merchant(self, name: str) -> str:
        return name.split("  ")[0].strip()[:80]

    def _categorize(self, name: str, trans_type: str) -> str:
        n = name.upper()
        t = trans_type.upper()

        if "ELECTRONIC DEPOSIT" in t or "P&G" in n:
            return "Income"
        if "HEARTLAND" in n or "MORTGAGE" in n:
            return "Mortgage"
        if "SANTANDER" in n:
            return "Auto Loan"
        if "VW CREDIT" in n:
            return "Auto Loan"
        if "TESLA" in n:
            return "Auto Loan"
        if "AFFIRM" in n:
            return "BNPL Payment"
        if "LIGHTSTREAM" in n:
            return "Personal Loan"
        if "AMEX" in n or "APPLE CARD" in n or "GSBANK" in n:
            return "CC Payment"
        if "CREDIT CARD" in n:
            return "CC Payment"
        if "ROBINHOOD" in n:
            return "Investing"
        if "ATM" in t:
            return "Cash"
        if any(k in n for k in ["KROGER", "WHOLE FOODS", "COSTCO"]):
            return "Groceries"
        if "WIRE TRANSFER" in t:
            return "Transfer"
        if "MOBILE BANKING TRANSFER" in t:
            return "Transfer"
        return "Other"
