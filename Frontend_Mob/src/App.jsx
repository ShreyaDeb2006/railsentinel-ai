import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import RPFMobile from "./pages/RPFMobile";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/rpf" element={<RPFMobile />} />
        <Route
          path="*"
          element={
            <div style={{ padding: 40, color: "#8695ae" }}>
              Not found. <Link to="/">Go to dashboard</Link> or{" "}
              <Link to="/rpf">RPF app</Link>.
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
