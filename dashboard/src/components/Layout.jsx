import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Shield, Activity, ShieldAlert, Settings, Zap, List, MessageSquare, Database } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

const fetchMetrics = async () => {
  const res = await fetch('/api/metrics');
  if (!res.ok) return null;
  return res.json();
};

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) return null;
  return res.json();
};

const Layout = ({ children }) => {
  const { t } = useTranslation();
  const location = useLocation();

  const getTabClass = (path) => {
    const isActive = location.pathname.startsWith(path);
    if (path === '/quarantine') {
      return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-red-500/10 text-red-400' : 'text-gray-400 hover:text-gray-200'}`;
    }
    return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'text-gray-400 hover:text-gray-200'}`;
  };

  const queryClient = useQueryClient();
  const { data: metrics } = useQuery({ queryKey: ['metrics'], queryFn: fetchMetrics, refetchInterval: 3000 });
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 10000 });

  const mutation = useMutation({
    mutationFn: async (newConfig) => {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({...config, ...newConfig})
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    }
  });

  const llmPercent = metrics ? (metrics.llm_requests_current_min / metrics.llm_rate_limit) * 100 : 0;

  return (
    <div className="min-h-screen p-8 font-sans">
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Shield className="w-12 h-12 text-[#58a6ff]" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">SentinelCell</h1>
            <p className="text-sm text-gray-400">MAS Command Center</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span className="font-semibold text-green-400">Live Telemetry</span>
        </div>
      </header>

      {/* Mode Switcher & Limits Monitor */}
      <div className="bg-gray-900 border border-white/10 rounded-lg p-4 mb-8 flex flex-col md:flex-row gap-6 justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400 font-semibold uppercase tracking-wider">Mode</span>
          <button
            onClick={() => {
              const newVal = config?.PASSIVE_MONITORING === "true" ? "false" : "true";
              mutation.mutate({ PASSIVE_MONITORING: newVal });
            }}
            disabled={mutation.isPending || !config}
            className={`px-4 py-2 rounded-md font-bold transition-all ${config?.PASSIVE_MONITORING === "true" ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/50' : 'bg-red-500/20 text-red-500 border border-red-500/50'}`}
          >
            {config?.PASSIVE_MONITORING === "true" ? '👀 Sniffer Mode (Passive)' : '🛡️ Guardian Mode (Active)'}
          </button>
        </div>

        <div className="flex gap-8 items-center w-full md:w-auto">
          <div className="w-full md:w-48">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-400">LLM Rate Limit</span>
              <span className="text-gray-200">{metrics?.llm_requests_current_min || 0} / {metrics?.llm_rate_limit || 50}</span>
            </div>
            <div className="h-2 bg-black rounded-full overflow-hidden border border-white/5">
              <div
                className={`h-full ${llmPercent > 80 ? 'bg-red-500' : 'bg-blue-500'} transition-all`}
                style={{width: `${Math.min(llmPercent, 100)}%`}}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-4 mb-8 border-b border-gray-800 pb-2 overflow-x-auto">
        <NavLink to="/dashboard" className={getTabClass('/dashboard')}>
          <Activity className="w-5 h-5" />
          {t('sidebar.dashboard')}
        </NavLink>
        <NavLink to="/settings" className={getTabClass('/settings')}>
          <Settings className="w-5 h-5" />
          {t('sidebar.settings')}
        </NavLink>
        <NavLink to="/quarantine" className={getTabClass('/quarantine')}>
          <ShieldAlert className="w-5 h-5" />
          {t('sidebar.quarantine')}
        </NavLink>
        <NavLink to="/schemas" className={getTabClass('/schemas')}>
          <Database className="w-5 h-5" />
          {t('sidebar.schemas')}
        </NavLink>
        <NavLink to="/audit" className={getTabClass('/audit')}>
          <List className="w-5 h-5" />
          {t('sidebar.audit_logs')}
        </NavLink>
        <NavLink to="/chat" className={getTabClass('/chat')}>
          <MessageSquare className="w-5 h-5" />
          {t('sidebar.chat_test')}
        </NavLink>
        <NavLink to="/examples" className={getTabClass('/examples')}>
          <Zap className="w-5 h-5" />
          {t('sidebar.examples')}
        </NavLink>
      </div>

      <main>
        {children}
      </main>
    </div>
  );
};

export default Layout;
