from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    role: str = "normal"
    organization: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    organization: Optional[str] = None
    created_at: str
    last_login: str
    consent_given: bool
    preferences: dict = {"notifications": True, "emailAlerts": False}


class AuthResponse(BaseModel):
    user: UserResponse
    token: str
    refreshToken: str


class TokenRefreshRequest(BaseModel):
    refreshToken: str


class ConsentRequest(BaseModel):
    purpose: str
    retentionDays: int = 30
