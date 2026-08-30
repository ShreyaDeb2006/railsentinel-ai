"""
schemas.py
----------
These define the exact JSON shape each piece sends/receives —
this is the "data contract" everyone on the team agreed on.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GPS(BaseModel):
    lat: float
    lng: float


class CameraDetectionIn(BaseModel):
    device_id: str
    object_type: str
    confidence: float
    gps: GPS
    timestamp: Optional[datetime] = None


class HandheldReadingIn(BaseModel):
    device_id: str
    reading_type: str
    reading_value: float
    gps: GPS
    timestamp: Optional[datetime] = None


class VerifyIn(BaseModel):
    verified_by: str
    final_status: str  # e.g. "confirmed_threat" or "false_alarm"


class AlertOut(BaseModel):
    id: int
    threat_level: str
    camera_confidence: Optional[float]
    handheld_reading: Optional[float]
    object_type: Optional[str]
    lat: float
    lng: float
    device_ids: str
    status: str
    verified_by: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True