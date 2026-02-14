import uuid
import pandas as pd
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionSource, ImportBatch
from app.parsers.credit_card_6032 import CreditCard6032Parser
from app.parsers.apple_card import AppleCardParser
from app.parsers.amex import AmexParser
from app.parsers.checking_1569 import Checking1569Parser


PARSERS = [CreditCard6032Parser, AppleCardParser, AmexParser, Checking1569Parser]


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def detect_parser(self, file_path: str):
        df = pd.read_csv(file_path, nrows=1, dtype=str)
        columns = set(c.strip() for c in df.columns)
        for parser_cls in PARSERS:
            if parser_cls.EXPECTED_COLUMNS.issubset(columns):
                return parser_cls()
        raise ValueError(
            f"Unknown CSV format. Columns found: {columns}. "
            f"Supported formats: Credit Card 6032, Apple Card, AMEX, Checking 1569"
        )

    def get_or_create_source(self, parser) -> TransactionSource:
        source = self.db.query(TransactionSource).filter(
            TransactionSource.name == parser.SOURCE_NAME
        ).first()
        if not source:
            source = TransactionSource(
                name=parser.SOURCE_NAME,
                type=parser.SOURCE_TYPE,
                institution=parser.SOURCE_NAME,
                active=True,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source

    def import_csv(self, file_path: str, file_hash: str, filename: str) -> dict:
        parser = self.detect_parser(file_path)
        source = self.get_or_create_source(parser)
        raw_transactions = parser.parse(file_path)

        # Get existing hashes for this source to detect duplicates
        existing_hashes = set(
            h[0] for h in self.db.query(Transaction.dedup_hash).filter(
                Transaction.source_id == source.id,
                Transaction.dedup_hash.isnot(None),
            ).all()
        )

        batch_id = str(uuid.uuid4())
        imported = 0
        skipped = 0
        min_date = None
        max_date = None

        for txn_data in raw_transactions:
            dedup = txn_data.pop("dedup_hash", None)
            if dedup and dedup in existing_hashes:
                skipped += 1
                continue

            txn = Transaction(
                source_id=source.id,
                import_batch_id=batch_id,
                dedup_hash=dedup,
                **txn_data,
            )
            self.db.add(txn)
            imported += 1

            d = txn_data["transaction_date"]
            if min_date is None or d < min_date:
                min_date = d
            if max_date is None or d > max_date:
                max_date = d

        # Record the batch
        batch = ImportBatch(
            batch_id=batch_id,
            source_id=source.id,
            filename=filename,
            file_hash=file_hash,
            rows_imported=imported,
            rows_skipped=skipped,
            date_range_start=min_date,
            date_range_end=max_date,
        )
        self.db.add(batch)
        self.db.commit()

        return {
            "batch_id": batch_id,
            "filename": filename,
            "source_name": source.name,
            "rows_imported": imported,
            "rows_skipped": skipped,
            "date_range_start": min_date,
            "date_range_end": max_date,
        }
