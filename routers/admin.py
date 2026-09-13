from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from database import get_db
from models.user import User
from models.analysis import Analysis
from models.call import Call
from models.activity_log import ActivityLog

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/config")
def get_config():
    return {
        "appName": "VoxVault",
        "version": "1.0.0",
        "maxFileSize": 25 * 1024 * 1024,
        "supportedFormats": ["audio/wav", "audio/mp3", "audio/flac", "audio/ogg", "audio/webm"],
        "maxDuration": 300,
        "minDuration": 3,
        "riskThresholds": {"low": 30, "medium": 70, "high": 100},
        "models": {"primary": "AASIST v2.1", "speaker": "ECAPA-TDNN", "feature": "RawNet2"}
    }


@router.get("/users")
def get_users(
    search: str = Query(None),
    role: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_filter)) | (User.email.ilike(search_filter))
        )

    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.created_at.desc()).all()

    result = []
    for user in users:
        analyses_count = db.query(func.count(Analysis.id)).filter(Analysis.user_id == user.id).scalar()
        calls_count = db.query(func.count(Call.id)).filter(Call.user_id == user.id).scalar()
        reports_count = db.query(func.count(Analysis.id)).filter(
            Analysis.user_id == user.id,
            Analysis.risk_level.in_(["HIGH", "MEDIUM"])
        ).scalar()
        login_count = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.action == "login"
        ).scalar()

        result.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization": user.organization,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "lastLogin": user.last_login.isoformat() if user.last_login else None,
            "consentGiven": user.consent_given,
            "stats": {
                "analyses": analyses_count,
                "calls": calls_count,
                "reports": reports_count,
                "logins": login_count
            }
        })

    return {"users": result, "total": len(result)}


@router.get("/users/{user_id}")
def get_user_detail(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}, 404

    analyses_count = db.query(func.count(Analysis.id)).filter(Analysis.user_id == user.id).scalar()
    calls_count = db.query(func.count(Call.id)).filter(Call.user_id == user.id).scalar()
    reports_count = db.query(func.count(Analysis.id)).filter(
        Analysis.user_id == user.id,
        Analysis.risk_level.in_(["HIGH", "MEDIUM"])
    ).scalar()

    recent_analyses = db.query(Analysis).filter(Analysis.user_id == user.id)\
        .order_by(Analysis.created_at.desc()).limit(10).all()

    recent_activities = db.query(ActivityLog).filter(ActivityLog.user_id == user.id)\
        .order_by(ActivityLog.created_at.desc()).limit(20).all()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization": user.organization,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "lastLogin": user.last_login.isoformat() if user.last_login else None,
            "consentGiven": user.consent_given,
        },
        "stats": {
            "analyses": analyses_count,
            "calls": calls_count,
            "reports": reports_count
        },
        "recentAnalyses": [
            {
                "id": a.id,
                "riskScore": a.risk_score,
                "riskLevel": a.risk_level,
                "status": a.status,
                "createdAt": a.created_at.isoformat() if a.created_at else None
            }
            for a in recent_analyses
        ],
        "recentActivities": [
            {
                "id": al.id,
                "action": al.action,
                "details": al.details,
                "createdAt": al.created_at.isoformat() if al.created_at else None
            }
            for al in recent_activities
        ]
    }


@router.put("/users/{user_id}/role")
def update_user_role(user_id: str, body: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found"}, 404

    new_role = body.get("role")
    if new_role not in ["normal", "operator", "government", "admin"]:
        return {"error": "Invalid role"}, 400

    user.role = new_role
    db.commit()
    return {"message": f"User role updated to {new_role}", "user": {"id": user.id, "role": user.role}}


@router.get("/usage")
def get_usage(db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar()
    total_analyses = db.query(func.count(Analysis.id)).scalar()
    total_calls = db.query(func.count(Call.id)).scalar()

    high_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "HIGH").scalar()
    medium_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "MEDIUM").scalar()
    low_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "LOW").scalar()

    avg_processing = db.query(func.avg(Analysis.processing_time_ms)).filter(
        Analysis.status == "completed"
    ).scalar() or 0

    daily_usage = []
    for i in range(6, -1, -1):
        date = datetime.now(timezone.utc).date() - timedelta(days=i)
        day_start = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        day_analyses = db.query(func.count(Analysis.id)).filter(
            Analysis.created_at >= day_start,
            Analysis.created_at < day_end
        ).scalar()

        day_users = db.query(func.count(func.distinct(Analysis.user_id))).filter(
            Analysis.created_at >= day_start,
            Analysis.created_at < day_end
        ).scalar()

        daily_usage.append({
            "date": date.isoformat(),
            "analyses": day_analyses,
            "users": day_users
        })

    role_distribution = []
    for role in ["normal", "operator", "government", "admin"]:
        count = db.query(func.count(User.id)).filter(User.role == role).scalar()
        role_distribution.append({"role": role, "count": count})

    return {
        "totalUsers": total_users,
        "totalAnalyses": total_analyses,
        "totalCalls": total_calls,
        "avgProcessingTimeMs": round(avg_processing),
        "riskDistribution": {
            "high": high_risk,
            "medium": medium_risk,
            "low": low_risk
        },
        "roleDistribution": role_distribution,
        "dailyUsage": daily_usage
    }


@router.get("/activity")
def get_activity(
    user_id: str = Query(None),
    action: str = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    query = db.query(ActivityLog)

    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if action:
        query = query.filter(ActivityLog.action == action)

    activities = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()

    result = []
    for act in activities:
        user = db.query(User).filter(User.id == act.user_id).first()
        result.append({
            "id": act.id,
            "userId": act.user_id,
            "userName": user.name if user else "Unknown",
            "userEmail": user.email if user else "Unknown",
            "action": act.action,
            "details": act.details,
            "createdAt": act.created_at.isoformat() if act.created_at else None
        })

    return {"activities": result, "total": len(result)}


@router.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Analysis).filter(
        Analysis.risk_level.in_(["HIGH", "MEDIUM"])
    ).order_by(Analysis.created_at.desc()).limit(50).all()

    result = []
    for r in reports:
        user = db.query(User).filter(User.id == r.user_id).first() if r.user_id else None
        result.append({
            "id": r.id,
            "riskScore": r.risk_score,
            "riskLevel": r.risk_level,
            "confidence": r.confidence,
            "callerNumber": r.caller_number,
            "city": r.city,
            "state": r.state,
            "status": r.status,
            "filedBy": {
                "id": user.id if user else None,
                "name": user.name if user else "System",
                "email": user.email if user else None
            } if user or r.user_id else None,
            "createdAt": r.created_at.isoformat() if r.created_at else None
        })

    return {"reports": result, "total": len(result)}
