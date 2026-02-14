from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    parent_category = Column(String)
    budget_category = Column(String)
    color_code = Column(String)
    is_discretionary = Column(Boolean, default=True)
    is_essential = Column(Boolean, default=False)


class CategoryMapping(Base):
    __tablename__ = "category_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_pattern = Column(String, nullable=False)
    source_category = Column(String)
    mapped_category = Column(String, nullable=False)
