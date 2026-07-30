from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from app.db.index import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    item = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
