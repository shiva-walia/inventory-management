from fastapi import FastAPI, Depends
from app.routers import products, categories, suppliers, transactions, reports, auth
from app.routers.auth import get_current_user

app = FastAPI(
    title="Inventory Management API",
    description="Stock tracking with PostgreSQL triggers, audit logs, JWT auth, and low-stock alerts.",
    version="2.0.0",
)

# Public routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected routes
app.include_router(categories.router,   prefix="/categories",   tags=["Categories"],  dependencies=[Depends(get_current_user)])
app.include_router(suppliers.router,    prefix="/suppliers",    tags=["Suppliers"],   dependencies=[Depends(get_current_user)])
app.include_router(products.router,     prefix="/products",     tags=["Products"],    dependencies=[Depends(get_current_user)])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"],dependencies=[Depends(get_current_user)])
app.include_router(reports.router,      prefix="/reports",      tags=["Reports"],     dependencies=[Depends(get_current_user)])

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Inventory API running"}