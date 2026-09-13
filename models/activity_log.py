import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # login, logout, upload, report, escalate, block, flag
    details = Column(Text, nullable=True)  # JSON string with extra info
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
