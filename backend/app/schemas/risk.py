from pydantic import BaseModel


class RiskOut(BaseModel):
    category: str
    title: str
    reason: str
    severity: str
    recommendation: str
    score: float

    class Config:
        from_attributes = True
