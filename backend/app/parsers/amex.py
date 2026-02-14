import pandas as pd
from typing import List, Dict
from app.parsers.base_parser import BaseParser


class AmexParser(BaseParser):
    SOURCE_NAME = "AMEX"
    SOURCE_TYPE = "credit_card"
    EXPECTED_COLUMNS = {"Date", "Description", "Amount", "Category"}

    def parse(self, file_path: str) -> List[Dict]:
        df = pd.read_csv(file_path, dtype=str)
        df.columns = df.columns.str.strip()
        transactions = []
        for _, row in df.iterrows():
            date_str = str(row.get("Date", "")).strip()
            if not date_str or date_str == "nan":
                continue
            description = str(row.get("Description", "")).strip()
            try:
                amount = float(str(row.get("Amount", "0")).replace(",", ""))
            except ValueError:
                continue

            is_debit = amount > 0
            category = str(row.get("Category", "")).strip() if pd.notna(row.get("Category")) else None
            card_member = str(row.get("Card Member", "")).strip() if pd.notna(row.get("Card Member")) else None
            extended = str(row.get("Extended Details", "")).strip() if pd.notna(row.get("Extended Details")) else None
            address = str(row.get("Address", "")).strip() if pd.notna(row.get("Address")) else None
            city_state = str(row.get("City/State", "")).strip() if pd.notna(row.get("City/State")) else None
            zip_code = str(row.get("Zip Code", "")).strip() if pd.notna(row.get("Zip Code")) else None
            country = str(row.get("Country", "")).strip() if pd.notna(row.get("Country")) else None
            reference = str(row.get("Reference", "")).strip() if pd.notna(row.get("Reference")) else None

            normalized_cat = self._normalize_category(category) if category else "Other"

            transactions.append({
                "transaction_date": pd.to_datetime(date_str).date(),
                "description": description,
                "merchant": description[:80],
                "category": normalized_cat,
                "original_category": category,
                "transaction_type": "charge" if is_debit else "credit",
                "amount": abs(amount),
                "is_debit": is_debit,
                "card_member": card_member,
                "extended_details": extended,
                "address": address,
                "city_state": city_state,
                "zip_code": zip_code,
                "country": country,
                "reference_number": reference,
                "dedup_hash": self.make_dedup_hash(self.SOURCE_NAME, date_str, str(amount), description),
            })
        return transactions

    def _normalize_category(self, cat: str) -> str:
        mapping = {
            "Merchandise & Supplies-Groceries": "Groceries",
            "Merchandise & Supplies-Internet Purchase": "Shopping",
            "Restaurant-Restaurant": "Dining",
            "Transportation-Fuel": "Transportation",
            "Transportation-Taxis & Coach": "Transportation",
            "Business Services-Health Care Services": "Health",
            "Business Services-Professional Services": "Services",
            "Business Services-Utilities": "Utilities",
            "Fees & Adjustments-Fees & Adjustments": "Interest/Fees",
        }
        for key, val in mapping.items():
            if key.lower() in cat.lower():
                return val
        if "merchandise" in cat.lower():
            return "Shopping"
        if "restaurant" in cat.lower():
            return "Dining"
        if "business" in cat.lower():
            return "Services"
        if "transportation" in cat.lower():
            return "Transportation"
        if "fee" in cat.lower() or "interest" in cat.lower():
            return "Interest/Fees"
        return "Other"
