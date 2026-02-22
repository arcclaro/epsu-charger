import { StrictMode, lazy, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import './index.css';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const StationDetail = lazy(() => import('@/pages/StationDetail'));
const StationAwaiting = lazy(() => import('@/pages/StationAwaiting'));
const WorkOrderList = lazy(() => import('@/pages/WorkOrderList'));
const WorkOrderDetail = lazy(() => import('@/pages/WorkOrderDetail'));
const JobStart = lazy(() => import('@/pages/JobStart'));
const JobProgress = lazy(() => import('@/pages/JobProgress'));
const JobTask = lazy(() => import('@/pages/JobTask'));
const Admin = lazy(() => import('@/pages/Admin'));
const Sessions = lazy(() => import('@/pages/Sessions'));
const StationTest = lazy(() => import('@/pages/StationTest'));

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Page><Dashboard /></Page>} />
          <Route path="station/:id" element={<Page><StationDetail /></Page>} />
          <Route path="station/:id/awaiting" element={<Page><StationAwaiting /></Page>} />
          <Route path="station/:id/test" element={<Page><StationTest /></Page>} />
          <Route path="work-orders" element={<Page><WorkOrderList /></Page>} />
          <Route path="work-orders/:woId" element={<Page><WorkOrderDetail /></Page>} />
          <Route path="work-orders/:woId/items/:itemId/start-job" element={<Page><JobStart /></Page>} />
          <Route path="jobs/:jobId" element={<Page><JobProgress /></Page>} />
          <Route path="jobs/:jobId/tasks/:taskId" element={<Page><JobTask /></Page>} />
          <Route path="admin" element={<Page><Admin /></Page>} />
          <Route path="sessions" element={<Page><Sessions /></Page>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function Page({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingSpinner text="Loading..." />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
