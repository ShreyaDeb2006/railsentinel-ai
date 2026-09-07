import { NavLink } from "react-router-dom";
import { LayoutDashboard, Bell, Cpu } from "lucide-react";

/**
 * HOW TO CUSTOMIZE THESE ICONS
 * ----------------------------
 * These come from lucide-react, a free icon library already installed
 * in this project. To swap one out:
 *   1. Browse icons at https://lucide.dev/icons
 *   2. Import the one you want at the top of this file, e.g.:
 *        import { LayoutDashboard, Bell, Cpu, Radar } from "lucide-react";
 *   3. Use it in the NAV_ITEMS list below instead of the current icon.
 *
 * To use your OWN icon (an image or custom SVG) instead of a library icon,
 * replace the `icon` value with a small component that renders an <img>
 * or inline <svg>, e.g.:
 *   { label: "Dashboard", icon: () => <img src="/icons/dashboard.svg" width={18} />, path: "/" }
 */
const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/", end: true },
  { label: "Alerts", icon: Bell, path: "/alerts" },
  { label: "Devices", icon: Cpu, path: "/devices" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ label, icon: Icon, path, end }) => (
          <NavLink
            key={path}
            to={path}
            end={end}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <Icon size={18} strokeWidth={2} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
