RailSentinel AI - Frontend
===========================

There are two separate pages in this project:

1) React dashboard/RPF app (index.html -> src/App.jsx)
   - This is the main app: the desk Dashboard and the RPF mobile
     verification flow (react-router, at "/" and "/rpf").
   - Run with Vite:
       npm install
       npm run dev
     Then open the URL Vite prints (usually http://localhost:5173/).

2) Standalone field page (field.html)
   - A single, dependency-free HTML/JS page with its own alert feed,
     verify buttons, and manual "Report Alert" form. Does not use
     React or Vite's dev server features.
   - Two ways to run it:
       a) With the Vite dev server already running (see above), just
          open http://localhost:5173/field.html
       b) Or serve it standalone with Python, no npm needed:
            cd "path to Frontend_Mob"
            py -m http.server 5500
          then open http://localhost:5500/field.html

Backend
-------
Both pages talk to the FastAPI backend over HTTP + WebSocket.
Start it first:
    cd backend
    uvicorn main:app --reload
(defaults to http://127.0.0.1:8000)

- The React app's backend URL is set in src/api.js (API_BASE / WS_URL).

If index file doesnot open, add "/field.html" to the end of the localhost url
- field.html's backend URL is set via its in-app Settings sheet
  (gear icon, top right) - defaults to http://127.0.0.1:8000.
  Enter just the bare origin there, with no path (not .../docs).
