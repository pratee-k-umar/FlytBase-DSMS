import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import DeviceRestriction from "./components/common/DeviceRestriction";
import Layout from "./components/common/Layout";
import Analytics from "./pages/Analytics";
import Bases from "./pages/Bases";
import Drone from "./pages/Drone";
import LiveMonitor from "./pages/LiveMonitor";
import MissionPlanner from "./pages/MissionPlanner";
import Missions from "./pages/Missions";

function App() {
  return (
    <DeviceRestriction>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/bases" replace />} />
            <Route path="drones" element={<Drone />} />
            <Route path="missions" element={<Missions />} />
            <Route path="mission/planner" element={<MissionPlanner />} />
            <Route path="mission/monitor" element={<LiveMonitor />} />
            <Route path="bases" element={<Bases />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="*" element={<Navigate to="/bases" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </DeviceRestriction>
  );
}

export default App;
