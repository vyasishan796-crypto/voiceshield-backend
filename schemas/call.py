from pydantic import BaseModel
from typing import Optional, List


class CallNote(BaseModel):
    id: str
    content: str
    createdAt: str
    author: str


class Indicator(BaseModel):
    type: str
    description: str
    severity: str


class OperatorCall(BaseModel):
    id: str
    sessionId: str
    callerNumber: str
    duration: int
    status: str
    riskScore: int
    riskLevel: str
    deepfakeProbability: float
    speakerConsistency: float
    confidence: float
    indicators: List[Indicator]
    startedAt: str
    endedAt: Optional[str] = None
    escalatedAt: Optional[str] = None
    blockedAt: Optional[str] = None
    notes: List[CallNote] = []


class OperatorCallList(BaseModel):
    calls: List[OperatorCall]
    total: int
    page: int
    limit: int
    totalPages: int


class OperatorStats(BaseModel):
    activeCalls: int
    highRiskToday: int
    escalatedToday: int
    blockedNumbers: int
    riskDistribution: dict


class ThreatFeedItem(BaseModel):
    id: str
    callerNumber: str
    riskLevel: str
    riskScore: int
    timestamp: str
    status: str


class EscalationPayload(BaseModel):
    notes: str = ""
    priority: str = "medium"


class BlockPayload(BaseModel):
    reason: str = ""
    permanent: bool = False
