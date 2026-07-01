import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import { ToastProvider } from './components/Toast';

// Lazy loaded pages for Code Splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Quarantine = React.lazy(() => import('./pages/Quarantine'));
const Settings = React.lazy(() => import('./pages/Settings'));
const AuditLogs = React.lazy(() => import('./pages/AuditLogs'));
const ChatTest = React.lazy(() => import('./pages/ChatTest'));
const SchemaRegistry = React.lazy(() => import('./pages/SchemaRegistry'));
const Examples = React.lazy(() => import('./pages/Examples'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', background: 'linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))', color: 'var(--text-color)', minHeight: '100vh', fontFamily: 'Inter, monospace' }}>
          <div style={{ maxWidth: 900, margin: '0 auto' }} className="glass-panel p-6">
            <h2 style={{ fontSize: 22, marginBottom: 8 }}>Uh oh — bir hata oluştu.</h2>
            <p style={{ opacity: 0.9 }}>Uygulamada beklenmeyen bir hata yakalandı. Lütfen sayfayı yenileyin veya geliştirici konsolunu kontrol edin.</p>
            <details style={{ whiteSpace: 'pre-wrap', marginTop: '12px' }}>
              <summary>Hata detaylarını göster</summary>
              <br />
              {this.state.error && this.state.error.toString()}
              <br />
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </details>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export interface WidgetErrorBoundaryProps {
  children: React.ReactNode;
  title?: string;
}

export class WidgetErrorBoundary extends React.Component<WidgetErrorBoundaryProps, { hasError: boolean }> {
  constructor(props: WidgetErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: any, errorInfo: any) {
    console.error("WidgetErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-panel p-4 border border-rose-500/30 bg-rose-950/20 text-rose-200 rounded-lg flex flex-col justify-center items-center h-full min-h-[120px] w-full">
          <span className="text-xs font-semibold uppercase tracking-wider text-rose-400 mb-1">
            {this.props.title || "Widget Error"}
          </span>
          <p className="text-xs opacity-80 text-center">Failed to load component</p>
        </div>
      );
    }
    return this.props.children;
  }
}

const Login = React.lazy(() => import('./pages/Login'));

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <BrowserRouter>
            <Suspense fallback={<div className="p-8"><div className="glass-panel p-4 animate-pulse">Loading module…</div></div>}>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="*"
                  element={
                    <AuthGuard>
                      <Layout>
                        <Suspense fallback={<div className="p-8"><div className="glass-panel p-4 animate-pulse">Loading view…</div></div>}>
                          <Routes>
                            <Route path="dashboard" element={<Dashboard />} />
                            <Route path="quarantine" element={<Quarantine />} />
                            <Route path="schemas" element={<SchemaRegistry />} />
                            <Route path="settings" element={<Settings />} />
                            <Route path="audit" element={<AuditLogs />} />
                            <Route path="chat" element={<ChatTest />} />
                            <Route path="examples" element={<Examples />} />
                            <Route path="*" element={<Navigate to="/dashboard" replace />} />
                          </Routes>
                        </Suspense>
                      </Layout>
                    </AuthGuard>
                  }
                />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;

// Simple client-side AuthGuard. If an HttpOnly session cookie is used the
// browser will send it automatically — here we detect the cookie presence and
// otherwise fall back to checking a localStorage sentinel_username value.
function AuthGuard({ children }: { children: React.ReactElement }) {
  const hasSessionCookie = document.cookie.split(';').some(c => c.trim().startsWith('sentinel_session='));
  const username = window.localStorage.getItem('sentinel_username');
  if (!hasSessionCookie && !username) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
