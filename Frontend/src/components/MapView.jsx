import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";

const LEVEL_COLOR = {
  low: "#2fbf6f",
  uncertain: "#f5a623",
  high: "#f0453f",
};

// CARTO now requires a free API key for their basemap tiles (as of Aug
// 2026) — see /CARTO_API_KEY_SETUP.md for how to get one. Copy .env.example
// to .env and put your key in VITE_CARTO_API_KEY.
//
// Without a key configured, this falls back to plain OpenStreetMap tiles
// (light theme, no key needed) instead of showing CARTO's "API KEY
// REQUIRED" watermark — so the app still works for teammates who haven't
// set up a key yet, it just won't be dark-themed until they do.
const CARTO_KEY = import.meta.env.VITE_CARTO_API_KEY;

const TILE_URL = CARTO_KEY
  ? `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`
  : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

const TILE_ATTRIBUTION = CARTO_KEY
  ? '&copy; OpenStreetMap contributors &copy; CARTO'
  : '&copy; OpenStreetMap contributors';

// Default view — replace with your actual deployment zone's coordinates.
const DEFAULT_CENTER = [28.6139, 77.209]; // New Delhi, placeholder
const DEFAULT_ZOOM = 12;

function FlyToSelected({ alert }) {
  const map = useMap();
  useEffect(() => {
    if (alert) {
      map.flyTo([alert.lat, alert.lng], Math.max(map.getZoom(), 15), {
        duration: 0.6,
      });
    }
  }, [alert, map]);
  return null;
}

// Leaflet measures its container once on load and caches that size. When
// the panel is enlarged/shrunk via CSS, the container changes size but
// Leaflet doesn't know — this nudges it to remeasure once the resize
// transition has finished, so tiles don't stay cropped/blank.
function InvalidateOnResize({ watch }) {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 250);
    return () => clearTimeout(t);
  }, [watch, map]);
  return null;
}

export default function MapView({ alerts, selectedId, onSelect, expanded }) {
  const selected = alerts.find((a) => a.id === selectedId) || null;

  return (
    <MapContainer
      center={DEFAULT_CENTER}
      zoom={DEFAULT_ZOOM}
      style={{ height: "100%", width: "100%", background: "#0b1220" }}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
      <FlyToSelected alert={selected} />
      <InvalidateOnResize watch={expanded} />
      {alerts.map((alert) => {
        const level = (alert.threat_level || "").toLowerCase();
        const color = LEVEL_COLOR[level] || "#8695ae";
        const isSelected = alert.id === selectedId;
        return (
          <CircleMarker
            key={alert.id}
            center={[alert.lat, alert.lng]}
            radius={isSelected ? 11 : 8}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: isSelected ? 0.9 : 0.6,
              weight: isSelected ? 3 : 1.5,
            }}
            eventHandlers={{
              click: () => onSelect(alert.id),
            }}
          >
            <Popup>
              <div style={{ fontFamily: "Inter, sans-serif", fontSize: 13 }}>
                <strong>{alert.object_type || alert.reading_type || "Unclassified"}</strong>
                <br />
                {alert.threat_level} · {alert.device_ids}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
