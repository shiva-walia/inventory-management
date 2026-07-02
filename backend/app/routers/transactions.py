from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.database import get_db
from app.models.models import StockTransaction
from app.schemas.schemas import TransactionCreate, TransactionOut
from typing import List
from pydantic import BaseModel
router = APIRouter()

VALID_TYPES = {"IN", "OUT", "ADJUST"}

@router.post("/", response_model=TransactionOut, status_code=201)
async def record_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    if data.txn_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"txn_type must be one of {VALID_TYPES}")
    try:
        txn = StockTransaction(**data.model_dump())
        db.add(txn)
        await db.commit()
        await db.refresh(txn)
        return txn
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TransactionOut])
async def list_transactions(
    product_id: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(StockTransaction).order_by(StockTransaction.created_at.desc()).limit(limit)
    if product_id:
        query = query.where(StockTransaction.product_id == product_id)
    result = await db.execute(query)
    return result.scalars().all()
    from pydantic import BaseModel

class BulkAdjustRequest(BaseModel):
    product_ids: list[int]
    quantity: int
    txn_type: str
    note: str = "Bulk adjustment"

@router.post("/bulk-adjust", status_code=200)
async def bulk_adjust(data: BulkAdjustRequest, db: AsyncSession = Depends(get_db)):
    """Calls the PostgreSQL stored procedure to adjust multiple products at once."""
    if data.txn_type not in {"IN", "OUT", "ADJUST"}:
        raise HTTPException(status_code=400, detail="txn_type must be IN, OUT, or ADJUST")
    try:
        await db.execute(
            text("CALL bulk_stock_adjust(:ids, :qty, :type, :note)"),
            {
                "ids": data.product_ids,
                "qty": data.quantity,
                "type": data.txn_type,
                "note": data.note
            }
        )
        await db.commit()
        return {"message": f"Bulk {data.txn_type} applied to {len(data.product_ids)} products"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/product-detail/{product_id}")
async def product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    """Calls the PostgreSQL function to get full product detail with stock status."""
    result = await db.execute(
        text("SELECT * FROM get_product_detail(:id)"),
        {"id": product_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)