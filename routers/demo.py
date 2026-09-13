import random
from fastapi import APIRouter
from services.analysis import analyze_voice

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/samples")
def get_samples():
    return [
        {"id": "sample-1", "name": "Genuine Human Voice", "description": "Natural speech pattern from a verified human speaker", "duration": 12, "format": "audio/wav"},
        {"id": "sample-2", "name": "AI-Generated Voice Clone", "description": "High-quality deepfake voice clone of a public figure", "duration": 8, "format": "audio/wav"},
        {"id": "sample-3", "name": "TTS Synthetic Speech", "description": "Text-to-speech generated audio with robotic artifacts", "duration": 15, "format": "audio/wav"},
        {"id": "sample-4", "name": "Spliced Audio", "description": "Manually edited audio with cut-and-paste segments", "duration": 10, "format": "audio/wav"},
    ]


@router.post("/analyze")
def analyze_demo():
    result = analyze_voice()
    return result
