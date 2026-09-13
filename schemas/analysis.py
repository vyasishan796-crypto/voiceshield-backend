from pydantic import BaseModel
from typing import Optional, List


class Indicator(BaseModel):
    type: str
    description: str
    severity: str


class WindowedScore(BaseModel):
    windowIndex: int
    startTime: float
    endTime: float
    riskScore: int
    riskLevel: str
    confidence: float


class DetectionResult(BaseModel):
    analysisId: str
    sessionId: str
    modelVersion: str
    riskScore: int
    riskLevel: str
    confidence: float
    deepfakeConfidence: float
    speakerMismatchScore: Optional[float] = None
    explanation: str
    indicators: List[Indicator]
    recommendedAction: str
    processingTimeMs: int
    windowedScores: Optional[List[WindowedScore]] = None
    temporalSmoothing: Optional[dict] = None


class VoiceAnalysisResponse(BaseModel):
    id: str
    sessionId: str
    source: str
    status: str
    riskScore: int
    riskLevel: str
    createdAt: str


class AnalysisHistoryResponse(BaseModel):
    analyses: List[VoiceAnalysisResponse]
    total: int
    page: int
    limit: int
    totalPages: int
