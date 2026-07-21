from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.index import check_connection, get_db
from app.models import Customer
from app.schemas import CustomerCreate, CustomerOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify the database connection when the app starts.

    Schema changes are managed by Alembic migrations (see alembic/), not by
    create_all, so run `alembic upgrade head` after pulling model changes.
    """
    try:
        check_connection()
        print("[OK] Database connection established.")
    except SQLAlchemyError as exc:
        print(f"[ERROR] Database connection failed: {exc}")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Report whether the PostgreSQL container is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except SQLAlchemyError as exc:
        return {"database": "error", "detail": str(exc)}


@app.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = Customer(name=customer.name, email=customer.email)
    db.add(db_customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")
    db.refresh(db_customer)
    return db_customer


@app.get("/customers", response_model=List[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).all()
