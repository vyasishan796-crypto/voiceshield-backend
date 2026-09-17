from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database import get_db
from models.analysis import Analysis
from models.call import Call
from models.user import User

router = APIRouter(prefix="/government", tags=["government"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total_analyses = db.query(Analysis).count()
    high_risk = db.query(Analysis).filter(Analysis.risk_level == "HIGH").count()
    reports = db.query(Analysis).filter(Analysis.risk_level.in_(["HIGH", "MEDIUM"])).count()
    active_investigations = db.query(Call).filter(Call.status == "escalated").count()

    return {
        "totalAnalyses": total_analyses,
        "highRiskCount": high_risk,
        "scamReportsReceived": reports,
        "activeInvestigations": active_investigations,
        "threatTrends": [
            {"date": "2026-09-04", "highRisk": 12, "mediumRisk": 28, "lowRisk": 60},
            {"date": "2026-09-05", "highRisk": 15, "mediumRisk": 32, "lowRisk": 53},
            {"date": "2026-09-06", "highRisk": 18, "mediumRisk": 25, "lowRisk": 57},
            {"date": "2026-09-07", "highRisk": 22, "mediumRisk": 30, "lowRisk": 48},
            {"date": "2026-09-08", "highRisk": 14, "mediumRisk": 28, "lowRisk": 58},
            {"date": "2026-09-09", "highRisk": 20, "mediumRisk": 35, "lowRisk": 45},
            {"date": "2026-09-10", "highRisk": high_risk, "mediumRisk": reports - high_risk, "lowRisk": total_analyses - reports},
        ]
    }


@router.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    analyses = db.query(Analysis).filter(Analysis.risk_level.in_(["HIGH", "MEDIUM"])).order_by(Analysis.created_at.desc()).limit(50).all()
    
    result = []
    for a in analyses:
        user = db.query(User).filter(User.id == a.user_id).first() if a.user_id else None
        result.append({
            "id": f"RPT-{a.id[:8]}",
            "analysisId": a.id,
            "callerNumber": a.caller_number or "Unknown",
            "riskScore": a.risk_score,
            "riskLevel": a.risk_level,
            "city": a.city or "Unknown",
            "state": a.state or "Unknown",
            "status": "under_review",
            "filedBy": {
                "id": user.id if user else None,
                "name": user.name if user else "System",
                "email": user.email if user else None
            } if user or a.user_id else None,
            "createdAt": a.created_at.isoformat() if a.created_at else ""
        })
    
    return result


@router.get("/suspicious-numbers")
def get_suspicious_numbers(db: Session = Depends(get_db)):
    from models.analysis import Analysis as A
    results = (
        db.query(
            A.caller_number,
            func.count(A.id).label("totalAnalyses"),
            func.sum(case((A.risk_level == "HIGH", 1), else_=0)).label("highRiskCount"),
            func.sum(case((A.risk_level == "MEDIUM", 1), else_=0)).label("mediumRiskCount")
        )
        .filter(A.caller_number.isnot(None), A.caller_number != "")
        .group_by(A.caller_number)
        .all()
    )

    numbers = []
    for r in results:
        if r[0]:
            numbers.append({
                "phoneNumber": r[0],
                "totalAnalyses": r[1],
                "highRiskCount": r[2] or 0,
                "mediumRiskCount": r[3] or 0,
                "firstSeen": "2026-09-01T00:00:00",
                "lastSeen": "2026-09-10T00:00:00",
                "flagged": (r[2] or 0) > 2,
                "reports": []
            })
    return numbers


@router.post("/suspicious-numbers/{number}/flag")
def flag_number(number: str):
    return {"success": True, "message": f"Number {number} flagged for investigation"}


@router.get("/threat-map")
def get_threat_map(db: Session = Depends(get_db)):
    """Get all analyses with location data for map visualization"""
    analyses = db.query(Analysis).filter(
        Analysis.latitude.isnot(None),
        Analysis.longitude.isnot(None)
    ).all()

    city_data = {}
    for a in analyses:
        city = a.city or "Unknown"
        state = a.state or "Unknown"
        lat = a.latitude or 20.5937
        lng = a.longitude or 78.9629
        risk_level = a.risk_level or "LOW"
        key = f"{city}_{state}"

        if key not in city_data:
            city_data[key] = {
                "city": city,
                "state": state,
                "latitude": lat,
                "longitude": lng,
                "totalThreats": 0,
                "highRiskCount": 0,
                "mediumRiskCount": 0,
                "lowRiskCount": 0,
            }

        city_data[key]["totalThreats"] += 1
        if risk_level == "HIGH":
            city_data[key]["highRiskCount"] += 1
        elif risk_level == "MEDIUM":
            city_data[key]["mediumRiskCount"] += 1
        else:
            city_data[key]["lowRiskCount"] += 1

    return list(city_data.values())


@router.get("/live-calls")
def get_live_calls(db: Session = Depends(get_db)):
    """Get recent calls with location data for live tracking"""
    calls = db.query(Call).filter(
        Call.latitude.isnot(None),
        Call.longitude.isnot(None)
    ).order_by(Call.started_at.desc()).limit(50).all()

    return [
        {
            "id": c.id,
            "callerNumber": c.caller_number,
            "city": c.city or "Unknown",
            "state": c.state or "Unknown",
            "latitude": c.latitude or 20.5937,
            "longitude": c.longitude or 78.9629,
            "riskScore": c.risk_score,
            "riskLevel": c.risk_level,
            "status": c.status,
            "startedAt": c.started_at.isoformat() if c.started_at else "",
        } for c in calls
    ]
