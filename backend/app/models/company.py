from app.core.database import Base
from sqlalchemy import Column, String, Text, ForeignKey


class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    name = Column(String)
    industry = Column(String, nullable=True)
    headquarters = Column(String, nullable=True)
    business_model = Column(Text, nullable=True)
    products = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
