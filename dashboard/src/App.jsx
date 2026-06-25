import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';

// Lazy loaded pages for Code Splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Quarantine = React.lazy(() => import('./pages/Quarantine'));
const Settings = React.lazy(() => import('./pages/Settings'));
const AuditLogs = React.lazy(() => import('./pages/AuditLogs'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', background: '#333', color: 'white', minHeight: '100vh', fontFamily: 'monospace' }}>
          <h2>Something went wrong in the React App.</h2>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
            <summary>Click for error details</summary>
            <br />
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo && this.state.errorInfo.componentStack}
          </details>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Layout>
            <Suspense fallback={<div className="p-8 text-blue-400 font-mono">Loading module...</div>}>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/quarantine" element={<Quarantine />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/audit" element={<AuditLogs />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
          </Layout>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
