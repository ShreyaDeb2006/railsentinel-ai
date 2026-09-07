# RailSentinel AI — Dashboard

Two screens, one React project:

- **`/`** — Control-room dashboard: clickable summary tiles, live map,
  recent alerts, device status placeholder, and a today's-threats donut.
- **`/alerts`** — Full alerts list, filterable (All / High / Uncertain / Low),
  grouped by date (Today / Yesterday / older dates).
- **`/devices`** — Placeholder for now.
- **`/rpf`** — RPF mobile screen: pending alerts → detail → confirm/dismiss.

All four share one `AlertsProvider` (`src/context/AlertsContext.jsx`), so
there's a single WebSocket connection for the whole app, not one per page.

## How to run it

```bash
npm install     # you'll need to re-run this since lucide-react (icons) was added
npm run dev
```

Then visit `http://localhost:5173` (dashboard), `/alerts` or `/devices`
Your teammate's backend needs to be running at the same time — see the main
project README for that.

## Customizing the sidebar icons

Icons come from **lucide-react**, already installed. To change one:

1. Browse the full icon set at https://lucide.dev/icons
2. Open `src/components/Sidebar.jsx`
3. Swap the import at the top (e.g. `import { LayoutDashboard, Bell, Cpu } from "lucide-react"`)
   for whichever icons you want, and update the `NAV_ITEMS` array to match.

To use a completely custom icon (your own SVG or image) instead of a library
icon, replace the `icon` value in `NAV_ITEMS` with a small component that
renders it — there's a commented example in `Sidebar.jsx`.

## How the dashboard tiles link to Alerts

Clicking a summary tile calls `navigate()` with a query param, e.g.
`/alerts?filter=HIGH`. The Alerts page reads that param on load and sets its
filter chip accordingly. "Total alerts" links to `/alerts` with no param,
which the Alerts page treats as "All" (its default).

## What's still a placeholder

- **Device status** (dashboard widget + `/devices` page) — the backend has
  no dedicated device-health endpoint yet, so both are left as empty
  placeholders per current scope. Wire these up once that endpoint exists.

## Other notes

- **Map default center** — `src/components/MapView.jsx` still centers on a
  placeholder location (New Delhi). Update `DEFAULT_CENTER` for your demo.
- **Threat colors** stay consistent everywhere: green = Low, amber =
  Uncertain, red = High — matches `fusion.py`'s classification.
- The RPF screen asks for an "Officer ID" once and remembers it in
  `localStorage`, sending it as `verified_by` on every verify action.
