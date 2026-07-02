from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import Category
from app.schemas.schemas import CategoryCreate, CategoryOut
from typing import List

router = APIRouter()

@router.get("/", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()

@router.post("/", response_model=CategoryOut, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = Category(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat

@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    cat = await db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()