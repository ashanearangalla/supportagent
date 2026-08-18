import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .agent_db import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    # References order.email loosely — no hard FK across databases, since
    # conversations lives in aromatichug_agent and order lives in
    # aromatichug_db. Nullable to support anonymous/guest chat sessions.
    customer_email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    messages = relationship(
        "Message", back_populates="conversation", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "tool"
    content = Column(Text, nullable=True)  # nullable: assistant tool-call messages may have no text
    # JSON-encoded list of tool calls the assistant requested in this
    # message, e.g. [{"id": "...", "name": "search_products", "arguments": {...}}]
    # Null for plain text messages.
    tool_calls_json = Column(Text, nullable=True)
    # For role="tool" messages: which tool call this result answers.
    tool_call_id = Column(String(64), nullable=True)
    # For role="tool" messages: which tool was executed.
    tool_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    conversation = relationship("Conversation", back_populates="messages")