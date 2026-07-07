from app.core.database import Base
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func


class ChatMessage(Base):
    """
    One turn of a persisted conversation, scoped to a single
    investigation. Both the user's question and the assistant's answer
    are stored as separate rows (role="user" / role="assistant") in
    chronological order, so a chat can be closed and reopened later
    with full history intact -- and so answer_question() can pull the
    last few turns back out as conversation context for follow-up
    questions ("what about last year?").
    """
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), index=True)
    role = Column(String)  # "user" | "assistant"
    content = Column(Text)
    sources = Column(JSON, nullable=True)  # list of ChatSource dicts, only set for assistant turns
    created_at = Column(DateTime(timezone=True), server_default=func.now())
