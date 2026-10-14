import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const PlayGround = lazy(() => import('@/pages/PlayGround'));
const Dashboards = lazy(() => import('@/pages/Dashboards'));
const SharedDashboard = lazy(() => import('@/pages/SharedDashboard'));
const NotFound = lazy(() => import('@/pages/NotFound'));

const RouteFallback = () => (
  <div className="flex min-h-dvh items-center justify-center">
    <Loader2 className="text-primary h-6 w-6 animate-spin" />
  </div>
);

const App = () => (
  <Suspense fallback={<RouteFallback />}>
    <Routes>
      <Route path="/" element={<PlayGround />} />
      <Route path="/playground" element={<Navigate to="/" replace />} />
      <Route path="/dashboards" element={<Dashboards />} />
      <Route path="/dashboards/:id" element={<Dashboards />} />
      <Route path="/shared/:token" element={<SharedDashboard />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  </Suspense>
);

export default App;
