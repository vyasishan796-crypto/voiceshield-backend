import random
import json
from datetime import datetime, timedelta, timezone
from database import SessionLocal, engine, Base
from models.user import User
from models.call import Call
from models.analysis import Analysis
from models.activity_log import ActivityLog
from services.auth import hash_password
from services.location import get_location_from_phone

PHONE_NUMBERS = [
    "+91-9876543210", "+91-9123456789", "+91-8765432100", "+91-9988776655",
    "+91-7766554433", "+91-8899776655", "+91-9012345678", "+91-9345678901",
    "+91-8456789012", "+91-9567890123", "+91-7678901234", "+91-8789012345",
    "+91-9890123456", "+91-7901234567", "+91-8012345678", "+91-9123456700",
    "+91-9234567012", "+91-8345670123", "+91-7456701234", "+91-9567012345",
    "+91-8678012345", "+91-7789012345", "+91-9890123000", "+91-8012300456",
]

INDICATORS_HIGH = [
    {"type": "Synthetic Voice", "description": "AI-generated voice patterns detected", "severity": "high"},
    {"type": "Voice Cloning", "description": "Voice clone artifacts found in audio", "severity": "high"},
    {"type": "Speaker Mismatch", "description": "Voice does not match claimed identity", "severity": "high"},
]
INDICATORS_MEDIUM = [
    {"type": "Spectral Anomaly", "description": "Unusual frequency patterns observed", "severity": "medium"},
    {"type": "Compression Artifacts", "description": "Audio compression inconsistencies detected", "severity": "medium"},
    {"type": "Unusual Behavior", "description": "Call pattern deviates from normal baseline", "severity": "medium"},
]
INDICATORS_LOW = [
    {"type": "Clean Audio", "description": "No significant anomalies detected", "severity": "low"},
]


def seed():
    # Drop all tables and recreate with new columns
    print("Dropping old tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables with new columns...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Seeding users...")
    users_data = [
        ("admin@voiceshield.com", "admin123", "System Admin", "admin"),
        ("operator@test.com", "123456", "Operator Demo", "operator"),
        ("government@test.com", "123456", "Rajesh Kumar", "government"),
        ("user@test.com", "123456", "Regular User", "normal"),
    ]
    user_ids = []
    for email, pwd, name, role in users_data:
        u = User(email=email, password_hash=hash_password(pwd), name=name, role=role,
                 last_login=datetime.now(timezone.utc), consent_given=True)
        db.add(u)
        db.flush()
        user_ids.append(u.id)

    print("Seeding calls with location data...")
    statuses = ["active"] * 12 + ["escalated"] * 4 + ["blocked"] * 3 + ["active"] * (len(PHONE_NUMBERS) - 19)
    random.shuffle(statuses)

    for i, phone in enumerate(PHONE_NUMBERS):
        risk = random.randint(5, 98)
        level = "LOW" if risk <= 30 else "MEDIUM" if risk <= 70 else "HIGH"
        deepfake = round(random.uniform(0.05, 0.95), 3)
        speaker = round(random.uniform(0.1, 0.98), 3)
        location = get_location_from_phone(phone)

        if level == "HIGH":
            indicators = random.sample(INDICATORS_HIGH, k=min(2, len(INDICATORS_HIGH)))
        elif level == "MEDIUM":
            indicators = random.sample(INDICATORS_MEDIUM, k=min(2, len(INDICATORS_MEDIUM)))
        else:
            indicators = [{"type": "Clean Audio", "description": "Normal voice patterns", "severity": "low"}]

        minutes_ago = random.randint(2, 120)
        started = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

        call = Call(
            session_id=f"VS-2026-{100 + i:06d}",
            caller_number=phone,
            duration=random.randint(15, 300),
            status=statuses[i],
            risk_score=risk,
            risk_level=level,
            deepfake_probability=deepfake,
            speaker_consistency=speaker,
            confidence=round(random.uniform(0.80, 0.99), 3),
            indicators_json=json.dumps(indicators),
            notes_json=json.dumps([]),
            user_id=user_ids[1],
            city=location["city"],
            state=location["state"],
            latitude=location["latitude"],
            longitude=location["longitude"],
            started_at=started
        )
        if statuses[i] == "escalated":
            call.escalated_at = started + timedelta(minutes=random.randint(1, 5))
            call.notes_json = json.dumps([{"id": "1", "content": "Escalated by operator", "createdAt": call.escalated_at.isoformat(), "author": "System"}])
        elif statuses[i] == "blocked":
            call.blocked_at = started + timedelta(minutes=random.randint(1, 10))
            call.notes_json = json.dumps([{"id": "1", "content": "Blocked: Confirmed deepfake", "createdAt": call.blocked_at.isoformat(), "author": "System"}])
        db.add(call)

    print("Seeding analyses with location data...")
    for i in range(35):
        risk = random.randint(5, 98)
        level = "LOW" if risk <= 30 else "MEDIUM" if risk <= 70 else "HIGH"
        deepfake = round(random.uniform(0.05, 0.95), 3)
        speaker_consistency = round(random.uniform(0.1, 0.98), 3)

        if level == "HIGH":
            indicators = random.sample(INDICATORS_HIGH, k=min(2, len(INDICATORS_HIGH)))
            explanation = "Voice analysis indicates high probability of synthetic or manipulated audio."
            action = "This call is likely a deepfake. Recommend blocking and reporting."
        elif level == "MEDIUM":
            indicators = random.sample(INDICATORS_MEDIUM, k=min(2, len(INDICATORS_MEDIUM)))
            explanation = "Some suspicious patterns detected in the voice analysis."
            action = "Proceed with caution. Verify caller identity."
        else:
            indicators = [{"type": "Clean Audio", "description": "No anomalies detected", "severity": "low"}]
            explanation = "Voice appears genuine with no significant anomalies."
            action = "No action required."

        minutes_ago = random.randint(5, 2000)
        created = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        phone = random.choice(PHONE_NUMBERS)
        location = get_location_from_phone(phone)

        analysis = Analysis(
            user_id=random.choice(user_ids),
            session_id=f"session_{1000 + i}",
            source=random.choice(["upload", "recording"]),
            status="completed",
            audio_format=random.choice(["audio/wav", "audio/mp3", "audio/webm"]),
            duration_seconds=random.uniform(3, 120),
            file_size_bytes=random.randint(50000, 2000000),
            risk_score=risk,
            risk_level=level,
            confidence=round(random.uniform(0.80, 0.99), 3),
            deepfake_confidence=deepfake,
            speaker_consistency=speaker_consistency,
            context_anomaly_score=round(random.uniform(0.0, 0.6), 3),
            explanation=explanation,
            indicators_json=json.dumps(indicators),
            recommended_action=action,
            processing_time_ms=random.randint(120, 450),
            caller_number=phone,
            city=location["city"],
            state=location["state"],
            latitude=location["latitude"],
            longitude=location["longitude"],
            created_at=created,
            completed_at=created + timedelta(seconds=random.randint(1, 5))
        )
        db.add(analysis)

    db.commit()

    print("Seeding activity logs...")
    actions = ["login", "upload", "report", "login", "upload", "login"]
    for i in range(20):
        user_id = random.choice(user_ids)
        action = random.choice(actions)
        minutes_ago = random.randint(5, 2000)
        created = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        
        if action == "login":
            details = "Logged in via web app"
        elif action == "upload":
            details = f"Uploaded audio sample_{random.randint(1, 100)}.wav"
        elif action == "report":
            details = f"Filed report for high-risk analysis"
        else:
            details = "System action"
        
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=f"192.168.1.{random.randint(1, 254)}",
            created_at=created
        )
        db.add(activity)

    db.commit()
    db.close()
    print("Seeding complete! 4 users, 24 calls, 35 analyses, 20 activities with location data.")


if __name__ == "__main__":
    seed()
