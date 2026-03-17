import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Header } from './shared/Header';
import { PlannerPage } from './planner/PlannerPage';
import { DashboardPage } from './dashboard/DashboardPage';

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', background: '#080808', color: '#e0e0e0' }}>
        <Header />
        <Routes>
          <Route path="/" element={<Navigate to="/planner" replace />} />
          <Route path="/planner" element={<PlannerPage />} />
          <Route path="/planner/:sessionId" element={<PlannerPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
