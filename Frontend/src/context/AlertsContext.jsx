import { createContext, useContext } from "react";
import { useAlerts } from "../hooks/useAlerts";

const AlertsContext = createContext(null);

export function AlertsProvider({ children }) {
  const value = useAlerts();
  return <AlertsContext.Provider value={value}>{children}</AlertsContext.Provider>;
}

export function useAlertsContext() {
  const ctx = useContext(AlertsContext);
  if (!ctx) {
    throw new Error("useAlertsContext must be used inside <AlertsProvider>");
  }
  return ctx;
}
