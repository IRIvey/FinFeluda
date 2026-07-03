from app.core.database import Base
from sqlalchemy import Column, String, Float, Text, ForeignKey


class Risk(Base):
    __tablename__ = "risks"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    category = Column(String)
    title = Column(String)
    reason = Column(Text)
    severity = Column(String)
    recommendation = Column(Text)
    score = Column(Float)
