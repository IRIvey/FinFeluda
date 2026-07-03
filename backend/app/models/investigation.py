from app.core.database import Base
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.sql import func
import enum

class InvestigationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"      # gather/normalize in progress
    gathered = "gathered"          # YOUR scope ends here -- data ready in Qdrant
    analyzing = "analyzing"        # teammate's REASON stage in progress
    completed = "completed"        # teammate's analysis done
    failed = "failed"

class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=True)
    status = Column(Enum(InvestigationStatus), default=InvestigationStatus.pending)
    health_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    source_type = Column(String)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())