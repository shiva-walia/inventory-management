from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db.database import get_db
from app.models.models import Product
from app.schemas.schemas import ProductCreate, ProductUpdate, ProductOut
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[ProductOut])
async def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%")
        )
    if category_id:
        query = query.where(Product.category_id == category_id)
    if low_stock:
        query = query.where(Product.stock_qty <= Product.reorder_level)
    offset = (page - 1) * page_size
    query = query.order_by(Product.id).offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def product_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT
            COUNT(*)                                                     AS total_products,
            SUM(stock_qty * unit_price)                                  AS total_inventory_value,
            SUM(CASE WHEN stock_qty = 0 THEN 1 ELSE 0 END)              AS out_of_stock,
            SUM(CASE WHEN stock_qty > 0 AND stock_qty <= reorder_level
                     THEN 1 ELSE 0 END)                                  AS low_stock,
            SUM(CASE WHEN stock_qty > reorder_level THEN 1 ELSE 0 END)  AS healthy
        FROM products
    """))
    row = result.mappings().one()
    return dict(row)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
