import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="normal")
    organization = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime, nullable=True)
