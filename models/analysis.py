import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True)
    source = Column(String, default="upload")
    audio_path = Column(String, nullable=True)
    audio_format = Column(String, default="audio/wav")
    duration_seconds = Column(Float, default=0.0)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String, default="processing")

    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="LOW")
    confidence = Column(Float, default=0.0)
    deepfake_confidence = Column(Float, default=0.0)
    speaker_consistency = Column(Float, default=0.0)
    context_anomaly_score = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    indicators_json = Column(Text, default="[]")
    recommended_action = Column(Text, default="")
    processing_time_ms = Column(Integer, default=0)
    model_version = Column(String, default="AASIST v2.1")

    caller_number = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
