import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.call import Call
from schemas.call import OperatorCallList, OperatorCall, OperatorStats, ThreatFeedItem, EscalationPayload, BlockPayload, Indicator, CallNote

router = APIRouter(prefix="/operator", tags=["operator"])


def call_to_response(call: Call) -> OperatorCall:
    indicators = json.loads(call.indicators_json) if call.indicators_json else []
    notes = json.loads(call.notes_json) if call.notes_json else []
    return OperatorCall(
        id=call.id,
        sessionId=call.session_id or "",
        callerNumber=call.caller_number,
        duration=call.duration,
        status=call.status,
        riskScore=call.risk_score,
        riskLevel=call.risk_level,
        deepfakeProbability=call.deepfake_probability,
        speakerConsistency=call.speaker_consistency,
        confidence=call.confidence,
        indicators=[Indicator(**i) for i in indicators],
        startedAt=call.started_at.isoformat() if call.started_at else "",
        endedAt=call.ended_at.isoformat() if call.ended_at else None,
        escalatedAt=call.escalated_at.isoformat() if call.escalated_at else None,
        blockedAt=call.blocked_at.isoformat() if call.blocked_at else None,
        notes=[CallNote(**n) for n in notes]
    )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    active = db.query(Call).filter(Call.status == "active").count()
    high_risk = db.query(Call).filter(Call.risk_level == "HIGH").count()
    escalated = db.query(Call).filter(Call.status == "escalated").count()
    blocked = db.query(Call).filter(Call.status == "blocked").count()

    low = db.query(Call).filter(Call.risk_level == "LOW").count()
    medium = db.query(Call).filter(Call.risk_level == "MEDIUM").count()
    high = db.query(Call).filter(Call.risk_level == "HIGH").count()
    total = low + medium + high or 1

    return OperatorStats(
        activeCalls=active,
        highRiskToday=high_risk,
        escalatedToday=escalated,
        blockedNumbers=blocked,
        riskDistribution={
            "low": round(low / total * 100),
            "medium": round(medium / total * 100),
            "high": round(high / total * 100)
        }
    )


@router.get("/threat-feed")
def get_threat_feed(db: Session = Depends(get_db)):
    calls = db.query(Call).filter(Call.status.in_(["active", "escalated"])).order_by(Call.started_at.desc()).limit(10).all()
    return [
        ThreatFeedItem(
            id=c.id,
            callerNumber=c.caller_number,
            riskLevel=c.risk_level,
            riskScore=c.risk_score,
            timestamp=c.started_at.isoformat() if c.started_at else "",
            status=c.status
        ) for c in calls
    ]


@router.get("/calls")
def get_calls(page: int = 1, limit: int = 20, risk_level: str = None, status: str = None, search: str = None, db: Session = Depends(get_db)):
    query = db.query(Call)
    if risk_level:
        query = query.filter(Call.risk_level == risk_level.upper())
    if status:
        query = query.filter(Call.status == status)
    if search:
        query = query.filter(Call.caller_number.contains(search) | Call.id.contains(search))

    total = query.count()
    calls = query.order_by(Call.started_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return OperatorCallList(
        calls=[call_to_response(c) for c in calls],
        total=total,
        page=page,
        limit=limit,
        totalPages=(total + limit - 1) // limit
    )


@router.get("/calls/{call_id}")
def get_call_detail(call_id: str, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call_to_response(call)


@router.post("/calls/{call_id}/escalate")
def escalate_call(call_id: str, payload: EscalationPayload, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = "escalated"
    call.escalated_at = datetime.now(timezone.utc)

    notes = json.loads(call.notes_json) if call.notes_json else []
    notes.append({
        "id": str(len(notes) + 1),
        "content": payload.notes or "Escalated by operator",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "author": "Operator"
    })
    call.notes_json = json.dumps(notes)

    db.commit()
    return {"success": True, "message": "Call escalated"}


@router.post("/calls/{call_id}/block")
def block_call(call_id: str, payload: BlockPayload, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call.status = "blocked"
    call.blocked_at = datetime.now(timezone.utc)

    notes = json.loads(call.notes_json) if call.notes_json else []
    notes.append({
        "id": str(len(notes) + 1),
        "content": f"Blocked. Reason: {payload.reason}" if payload.reason else "Blocked by operator",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "author": "Operator"
    })
    call.notes_json = json.dumps(notes)

    db.commit()
    return {"success": True, "message": "Caller blocked"}
