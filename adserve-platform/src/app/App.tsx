import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell }      from '@/components/layout/AppShell';
import { DemoPage }      from '@/components/demo/DemoPage';
import { AdsPage }       from '@/components/ads/AdsPage';
import { AnalyticsPage } from '@/components/analytics/AnalyticsPage';

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/"          element={<Navigate to="/demo" replace />} />
        <Route path="/demo"      element={<DemoPage />} />
        <Route path="/ads"       element={<AdsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </AppShell>
  );
}
