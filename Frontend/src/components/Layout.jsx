import { Outlet } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import Sidebar from "./Sidebar";
import { useAlertsContext } from "../context/AlertsContext";

export default function Layout() {
  const { connected } = useAlertsContext();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <ShieldCheck size={20} strokeWidth={2} />
          <span className="topbar-name">RailSentinel AI</span>
        </div>
        <div className={`system-status ${connected ? "online" : "offline"}`}>
          <span className="status-dot" />
          System status: {connected ? "Online" : "Offline"}
        </div>
      </header>

      <div className="app-body">
        <Sidebar />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
