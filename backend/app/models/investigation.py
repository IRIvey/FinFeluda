from app.core.database import Base
from sqlalchemy import Column, String, Float, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
import enum

class InvestigationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"      # gather/normalize in progress
    gathered = "gathered"          # data ready in Qdrant, REASON stage not run yet
    analyzing = "analyzing"        # REASON stage in progress
    completed = "completed"        # analysis done and persisted
    failed = "failed"

class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=True)
    status = Column(Enum(InvestigationStatus), default=InvestigationStatus.pending)
    health_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    financial_risk_score = Column(Float, nullable=True)
    operational_risk_score = Column(Float, nullable=True)
    business_risk_score = Column(Float, nullable=True)
    health_subscores = Column(JSON, nullable=True)  # {growth, liquidity, profitability, debt, efficiency}
    error_message = Column(Text, nullable=True)
    source_type = Column(String)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())