import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AlertsProvider } from "./context/AlertsContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Alerts from "./pages/Alerts";
import Devices from "./pages/Devices";

export default function App() {
  return (
    // One AlertsProvider wraps everything, so the whole app shares a
    // single WebSocket connection instead of each page opening its own.
    <AlertsProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/devices" element={<Devices />} />
          </Route>

          <Route
            path="*"
            element={
              <div style={{ padding: 40, color: "#8695ae" }}>
                Not found. <Link to="/">Go to dashboard</Link>.
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </AlertsProvider>
  );
}
