from app.core.database import Base
from sqlalchemy import Column, String, Float, Integer, ForeignKey


class Financial(Base):
    __tablename__ = "financials"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    year = Column(Integer)
    revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    expenses = Column(Float, nullable=True)
    assets = Column(Float, nullable=True)
    liabilities = Column(Float, nullable=True)
    cash_flow = Column(Float, nullable=True)
    debt = Column(Float, nullable=True)
    currency = Column(String, default="USD")
