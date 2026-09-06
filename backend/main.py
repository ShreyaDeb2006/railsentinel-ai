"""
main.py
-------
RailSentinel AI — Backend / "Brain" server.

Run with:
    uvicorn main:app --reload

Endpoints:
  POST /api/camera-detection    <- Person 2's camera module sends here
  POST /api/handheld-reading    <- Person 4's simulator sends here
  GET  /api/alerts              <- Person 3's dashboard fetches here
  POST /api/verify/{alert_id}   <- Person 5's mobile app sends here
  WS   /ws/alerts                <- Person 3's dashboard listens here for live updates
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import asyncio
import json

import models
import schemas
import fusion
from database import engine, get_db, Base, SessionLocal

# Creates the SQLite tables if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RailSentinel AI Backend")

# Allow the dashboard/mobile app (running on different ports) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a hackathon demo; tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# WebSocket connection manager — pushes new alerts to the dashboard live
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Background sweep — every few seconds, turn any lone reading that never
# found a pair (older than the matching time window) into its own alert,
# so nothing sits unmatched forever.
# ---------------------------------------------------------------------------
async def stale_sweep_loop():
    while True:
        await asyncio.sleep(5)
        db = SessionLocal()
        try:
            new_alerts = fusion.sweep_stale(db)
            for alert in new_alerts:
                await manager.broadcast({"type": "new_alert", "alert": _alert_to_dict(alert)})
        finally:
            db.close()


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(stale_sweep_loop())


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages FROM the dashboard, just keep the
            # connection open so we can push TO it.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Camera detection endpoint (Person 2 posts here)
# ---------------------------------------------------------------------------
@app.post("/api/camera-detection")
async def receive_camera_detection(data: schemas.CameraDetectionIn, db: Session = Depends(get_db)):
    detection = models.CameraDetection(
        device_id=data.device_id,
        object_type=data.object_type,
        confidence=data.confidence,
        lat=data.gps.lat,
        lng=data.gps.lng,
    )
    db.add(detection)
    db.commit()

    new_alert = fusion.try_fuse(db)
    if new_alert:
        await manager.broadcast({"type": "new_alert", "alert": _alert_to_dict(new_alert)})

    return {"status": "received", "detection_id": detection.id}


# ---------------------------------------------------------------------------
# Handheld reading endpoint (Person 4 posts here)
# ---------------------------------------------------------------------------
@app.post("/api/handheld-reading")
async def receive_handheld_reading(data: schemas.HandheldReadingIn, db: Session = Depends(get_db)):
    reading = models.HandheldReading(
        device_id=data.device_id,
        reading_type=data.reading_type,
        reading_value=data.reading_value,
        lat=data.gps.lat,
        lng=data.gps.lng,
    )
    db.add(reading)
    db.commit()

    new_alert = fusion.try_fuse(db)
    if new_alert:
        await manager.broadcast({"type": "new_alert", "alert": _alert_to_dict(new_alert)})

    return {"status": "received", "reading_id": reading.id}


# ---------------------------------------------------------------------------
# Alerts list endpoint (Person 3's dashboard fetches here)
# ---------------------------------------------------------------------------
@app.get("/api/alerts", response_model=List[schemas.AlertOut])
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).order_by(models.Alert.timestamp.desc()).all()
    return alerts


# ---------------------------------------------------------------------------
# Verify endpoint (Person 5's mobile app posts here)
# ---------------------------------------------------------------------------
@app.post("/api/verify/{alert_id}")
async def verify_alert(alert_id: int, data: schemas.VerifyIn, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = data.final_status
    alert.verified_by = data.verified_by
    db.commit()
    db.refresh(alert)

    await manager.broadcast({"type": "alert_updated", "alert": _alert_to_dict(alert)})

    return {"status": "updated", "alert_id": alert.id}


# ---------------------------------------------------------------------------
# Simple health check — useful for confirming the server is alive
# ---------------------------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "RailSentinel AI backend is running"}


def _alert_to_dict(alert: models.Alert) -> dict:
    return {
        "id": alert.id,
        "threat_level": alert.threat_level,
        "camera_confidence": alert.camera_confidence,
        "handheld_reading": alert.handheld_reading,
        "object_type": alert.object_type,
        "reading_type": alert.reading_type,
        "lat": alert.lat,
        "lng": alert.lng,
        "device_ids": alert.device_ids,
        "status": alert.status,
        "verified_by": alert.verified_by,
        "timestamp": alert.timestamp,
    }
