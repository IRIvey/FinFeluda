from pydantic import BaseModel
from typing import Optional


class CompanyOut(BaseModel):
    name: str
    industry: Optional[str]
    headquarters: Optional[str]
    business_model: Optional[str]
    products: Optional[str]
    summary: Optional[str]

    class Config:
        from_attributes = True
