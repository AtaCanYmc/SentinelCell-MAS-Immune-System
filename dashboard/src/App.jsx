import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';

// Lazy loaded pages for Code Splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Quarantine = React.lazy(() => import('./pages/Quarantine'));
const Settings = React.lazy(() => import('./pages/Settings'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Suspense fallback={<div className="p-8 text-blue-400 font-mono">Loading module...</div>}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/quarantine" element={<Quarantine />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
