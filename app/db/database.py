import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = "postgresql+asyncpg://postgres:RKyFZKjLGBprebyandamORWayoCvPZQw@reseau.proxy.rlwy.net:18187/railway"

print(f"Connecting to: {DATABASE_URL}")  # will show in terminal

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            print(f"DB ERROR: {e}")
            raise