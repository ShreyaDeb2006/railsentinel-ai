"""
models.py
---------
Defines the database tables:
- CameraDetection: raw data sent by the AI camera module (Person 2)
- HandheldReading: raw data sent by the handheld simulator (Person 4)
- Alert: the fused/classified result shown on the dashboard and mobile app
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from database import Base


class CameraDetection(Base):
    __tablename__ = "camera_detections"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    object_type = Column(String)
    confidence = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    matched = Column(Boolean, default=False)  # true once fused into an Alert


class HandheldReading(Base):
    __tablename__ = "handheld_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    reading_type = Column(String)
    reading_value = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    matched = Column(Boolean, default=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    threat_level = Column(String)  # "LOW", "UNCERTAIN", "HIGH"
    camera_confidence = Column(Float, nullable=True)
    handheld_reading = Column(Float, nullable=True)
    object_type = Column(String, nullable=True)  # from camera, e.g. "person"
    reading_type = Column(String, nullable=True)  # from handheld, e.g. "vibration"
    lat = Column(Float)
    lng = Column(Float)
    device_ids = Column(String)  # comma-separated, e.g. "cam_01,handheld_01"
    status = Column(String, default="pending_verification")
    verified_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
