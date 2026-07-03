from app.core.database import Base
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    executive_summary = Column(Text, nullable=True)
    financial_summary = Column(Text, nullable=True)
    risk_summary = Column(Text, nullable=True)
    opportunities = Column(Text, nullable=True)
    future_outlook = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    pdf_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
