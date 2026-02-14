from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TransactionSource(Base):
    __tablename__ = "transaction_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # credit_card, checking, savings
    last_four = Column(String)
    institution = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    transactions = relationship("Transaction", back_populates="source")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("transaction_sources.id"), nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    clearing_date = Column(Date)
    description = Column(String, nullable=False)
    merchant = Column(String, index=True)
    category = Column(String, index=True)
    original_category = Column(String)
    transaction_type = Column(String)  # debit, credit, purchase, payment
    amount = Column(Float, nullable=False)
    is_debit = Column(Boolean, nullable=False)
    memo = Column(Text)
    extended_details = Column(Text)
    address = Column(String)
    city_state = Column(String)
    zip_code = Column(String)
    country = Column(String)
    reference_number = Column(String)
    card_member = Column(String)
    purchased_by = Column(String)
    import_batch_id = Column(String, index=True)
    dedup_hash = Column(String, index=True)
    user_notes = Column(Text)
    is_excluded = Column(Boolean, default=False)
    imported_at = Column(DateTime, server_default=func.now())

    source = relationship("TransactionSource", back_populates="transactions")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String, unique=True, nullable=False)
    source_id = Column(Integer, ForeignKey("transaction_sources.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_hash = Column(String)
    rows_imported = Column(Integer)
    rows_skipped = Column(Integer)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    imported_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)

    source = relationship("TransactionSource")
