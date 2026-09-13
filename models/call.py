import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=True)
    caller_number = Column(String, nullable=False)
    duration = Column(Integer, default=0)
    status = Column(String, default="active")
    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="LOW")
    deepfake_probability = Column(Float, default=0.0)
    speaker_consistency = Column(Float, default=0.9)
    confidence = Column(Float, default=0.9)
    indicators_json = Column(Text, default="[]")
    notes_json = Column(Text, default="[]")
    user_id = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    blocked_at = Column(DateTime, nullable=True)
