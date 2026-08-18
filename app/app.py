
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db, metadata, get_columns, FORBIDDEN_TABLES


app = FastAPI(title="Customer Support Agent Service")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug/tables")
def list_tables():
    visible = sorted(set(metadata.tables.keys()) - FORBIDDEN_TABLES)
    return {"tables": visible}



@app.get("/debug/tables/{table_name}/columns")
def list_columns(table_name: str):
    """Shows the ALLOWLISTED columns only — this is what the agent can
    actually see, not the full DB schema."""
    try:
        columns = get_columns(table_name)
    except (ValueError, PermissionError, RuntimeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "table": table_name,
        "columns": [
            {"name": c.name, "type": str(c.type), "nullable": c.nullable}
            for c in columns
        ],
    }
    
@app.get("/debug/orders")
def sample_orders(limit: int = 5, db: Session = Depends(get_db)):
    try:
        columns = get_columns("order")
    except (ValueError, PermissionError, RuntimeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    stmt = select(*columns).limit(limit)
    rows = db.execute(stmt).mappings().all()
    return {"count": len(rows), "rows": [dict(r) for r in rows]}

@app.get("/debug/products")
def sample_products(limit: int = 5, db: Session = Depends(get_db)):
    try:
        columns = get_columns("product")
    except (ValueError, PermissionError, RuntimeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    stmt = select(*columns).limit(limit)
    rows = db.execute(stmt).mappings().all()
    return {"count": len(rows), "rows": [dict(r) for r in rows]}