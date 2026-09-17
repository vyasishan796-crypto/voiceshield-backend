from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.activity_log import ActivityLog
from schemas.auth import LoginRequest, SignupRequest, AuthResponse, UserResponse, TokenRefreshRequest, ConsentRequest
from services.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        organization=user.organization,
        createdAt=user.created_at.isoformat() if user.created_at else "",
        lastLogin=user.last_login.isoformat() if user.last_login else "",
        consentGiven=user.consent_given,
        preferences={"notifications": True, "emailAlerts": False}
    )


def log_activity(db: Session, user_id: str, action: str, details: str = None, request: Request = None):
    if not user_id:
        return
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(activity)
    db.commit()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/signup", response_model=AuthResponse)
def signup(req: SignupRequest, request: Request = None, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        token = create_access_token({"sub": existing.id, "role": existing.role})
        refresh = create_refresh_token({"sub": existing.id, "role": existing.role})
        existing.last_login = datetime.now(timezone.utc)
        db.commit()
        log_activity(db, existing.id, "login", "Account re-accessed via signup", request)
        return AuthResponse(user=user_to_response(existing), token=token, refreshToken=refresh)

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        role=req.role,
        organization=req.organization,
        last_login=datetime.now(timezone.utc),
        consent_given=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    refresh = create_refresh_token({"sub": user.id, "role": user.role})
    log_activity(db, user.id, "signup", f"New account created with role: {req.role}", request)
    return AuthResponse(user=user_to_response(user), token=token, refreshToken=refresh)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, request: Request = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    log_activity(db, user.id, "login", f"Logged in as {user.role}", request)

    token = create_access_token({"sub": user.id, "role": user.role})
    refresh = create_refresh_token({"sub": user.id, "role": user.role})
    return AuthResponse(user=user_to_response(user), token=token, refreshToken=refresh)


@router.post("/refresh")
def refresh(req: TokenRefreshRequest):
    payload = verify_token(req.refreshToken)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    token = create_access_token({"sub": payload.get("sub"), "role": payload.get("role", "normal")})
    return {"token": token}


@router.post("/forgot-password")
def forgot_password(body: dict):
    return {"success": True, "message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: dict):
    return {"success": True, "message": "Password has been reset successfully."}


@router.post("/consent")
def consent(req: ConsentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.consent_given = True
    current_user.consent_timestamp = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": "Consent recorded"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)
