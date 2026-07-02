from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.database import get_db
from app.schemas.schemas import LowStockAlert, InventorySummaryRow
from typing import List

router = APIRouter()

@router.get("/low-stock", response_model=List[LowStockAlert])
async def low_stock_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM low_stock_alerts"))
    return [LowStockAlert(**row) for row in result.mappings().all()]

@router.get("/inventory-summary", response_model=List[InventorySummaryRow])
async def inventory_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM inventory_summary"))
    return [InventorySummaryRow(**row) for row in result.mappings().all()]

@router.get("/audit-log")
async def audit_log(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM audit_log ORDER BY changed_at DESC LIMIT :limit"),
        {"limit": limit}
    )
    return result.mappings().all()