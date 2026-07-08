from app.core.database import Base
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func


class ComparisonChatMessage(Base):
    """
    One turn of a persisted conversation scoped to a PAIR of
    investigations (the two currently selected on the Compare page),
    mirroring ChatMessage but keyed on both investigation_id_a and
    investigation_id_b so a comparison chat can be reopened with full
    history intact, same as a single-investigation chat.
    """
    __tablename__ = "comparison_chat_messages"
    id = Column(String, primary_key=True)
    investigation_id_a = Column(String, ForeignKey("investigations.id"), index=True)
    investigation_id_b = Column(String, ForeignKey("investigations.id"), index=True)
    role = Column(String)  # "user" | "assistant"
    content = Column(Text)
    sources = Column(JSON, nullable=True)  # list of ComparisonChatSource dicts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
