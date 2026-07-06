from pydantic import BaseModel
from typing import Optional


class FinancialOut(BaseModel):
    year: int
    revenue: Optional[float]
    profit: Optional[float]
    expenses: Optional[float]
    assets: Optional[float]
    liabilities: Optional[float]
    cash_flow: Optional[float]
    debt: Optional[float]
    currency: str = "USD"

    class Config:
        from_attributes = True
