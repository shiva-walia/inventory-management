from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"
    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    products    = relationship("Product", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(150), nullable=False)
    contact_name = Column(String(100))
    email        = Column(String(150))
    phone        = Column(String(30))
    address      = Column(Text)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id            = Column(Integer, primary_key=True)
    sku           = Column(String(50), nullable=False, unique=True)
    name          = Column(String(200), nullable=False)
    description   = Column(Text)
    category_id   = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    unit_price    = Column(Numeric(12, 2), nullable=False)
    stock_qty     = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=10)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now())
    category      = relationship("Category", back_populates="products")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    id             = Column(Integer, primary_key=True)
    product_id     = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    txn_type       = Column(String(10), nullable=False)
    quantity       = Column(Integer, nullable=False)
    reference_note = Column(String(255))
    created_by     = Column(String(100), default="system")
    created_at     = Column(DateTime(timezone=True), server_default=func.now())