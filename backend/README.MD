# RailSentinel AI — Backend

This is the "brain" server. Everyone else's piece talks to this.

## Files
- `main.py` — the FastAPI app; all API routes + WebSocket live here
- `models.py` — database tables (CameraDetection, HandheldReading, Alert)
- `schemas.py` — the exact JSON shape each endpoint expects/returns (the "data contract")
- `fusion.py` — the threat-classification logic (Low/Uncertain/High)
- `database.py` — SQLite connection setup
- `requirements.txt` — Python packages needed

## How to run it

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server starts at: **http://127.0.0.1:8000**

Visit **http://127.0.0.1:8000/docs** for auto-generated interactive API docs —
you (and teammates) can test every endpoint from the browser, no Postman needed.

## Endpoints

| Method | URL | Who uses it | Purpose |
|---|---|---|---|
| POST | `/api/camera-detection` | Person 2 (camera) | Send a detected object |
| POST | `/api/handheld-reading` | Person 4 (simulator) | Send a sensor reading |
| GET | `/api/alerts` | Person 3 (dashboard) | Fetch all alerts |
| WS | `/ws/alerts` | Person 3 (dashboard) | Live alert push |
| POST | `/api/verify/{alert_id}` | Person 5 (mobile app) | Mark an alert verified |

## How fusion works
- When a camera detection or handheld reading arrives, the server checks if
  the *other* sensor also has a recent (within 30 sec), nearby unmatched
  reading. If yes → combines both into ONE alert.
- If no match yet, it waits.
- Every 5 seconds, a background sweep checks for readings that are now
  "too old" to ever be matched, and turns them into solo alerts instead of
  losing them.
- Threat level rules (in `fusion.py`, easy to tune):
  - **HIGH**: camera confidence ≥ 0.7 AND handheld reading ≥ 0.6
  - **UNCERTAIN**: either one is moderately high, or only one sensor reported
  - **LOW**: everything else

## Tested and confirmed working
- ✅ Paired camera + handheld → fuses into one HIGH alert
- ✅ Lone camera detection → becomes its own solo alert after ~5-8 sec
- ✅ Verify endpoint updates alert status correctly