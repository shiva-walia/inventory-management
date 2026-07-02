from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryOut(CategoryCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class SupplierOut(SupplierCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: float
    reorder_level: int = 10

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit_price: Optional[float] = None
    reorder_level: Optional[int] = None

class ProductOut(ProductCreate):
    id: int
    stock_qty: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    product_id: int
    txn_type: str
    quantity: int
    reference_note: Optional[str] = None
    created_by: Optional[str] = "system"

class TransactionOut(TransactionCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class LowStockAlert(BaseModel):
    id: int
    sku: str
    name: str
    stock_qty: int
    reorder_level: int
    category: Optional[str]
    units_needed: int

class InventorySummaryRow(BaseModel):
    category: Optional[str]
    total_products: int
    total_units: int
    total_value: float