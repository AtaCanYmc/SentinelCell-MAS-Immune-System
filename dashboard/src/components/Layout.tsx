import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Shield, Activity, ShieldAlert, Settings, Zap, List, MessageSquare, Database, Globe, Key } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { fetchWithAuth } from '../hooks/api';

const fetchMetrics = async () => {
  const res = await fetchWithAuth('/api/metrics');
  if (!res.ok) return null;
  return res.json();
};

const fetchConfig = async () => {
  const res = await fetchWithAuth('/api/config');
  if (!res.ok) return null;
  return res.json();
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { t, i18n } = useTranslation();
  const location = useLocation();

  const getTabClass = (path: string) => {
    const isActive = location.pathname.startsWith(path);
    if (path === '/quarantine') {
      return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-red-500/10 text-red-400' : 'text-gray-400 hover:text-gray-200'}`;
    }
    return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'text-gray-400 hover:text-gray-200'}`;
  };

  const queryClient = useQueryClient();
  const { data: metrics } = useQuery({ queryKey: ['metrics'], queryFn: fetchMetrics, refetchInterval: 3000 });
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 10000 });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [modalKeyInput, setModalKeyInput] = useState('');

  useEffect(() => {
    const hasKey = localStorage.getItem('sentinel_api_key');
    // If the config tells us there's an API key required but we don't have it in storage/cookie, show modal
    if (!hasKey && config && (config as Record<string, any>).API_KEY_SECRET) {
      // If we don't have sentinel_username in storage either
      if (!localStorage.getItem('sentinel_username')) {
        setShowAuthModal(true);
      }
    }
  }, [config]);

  const handleSaveKey = () => {
    if (modalKeyInput.trim()) {
      localStorage.setItem('sentinel_api_key', modalKeyInput.trim());
      setShowAuthModal(false);
      window.location.reload();
    }
  };

  const mutation = useMutation<any, Error, Record<string, any>>({
    mutationFn: async (newConfig) => {
      const res = await fetchWithAuth('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({...(config as Record<string, any> || {}), ...newConfig})
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
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-lg border border-white/10 text-xs">
            <Globe className="w-4 h-4 text-gray-400" />
            <select
              value={i18n.language}
              onChange={(e) => {
                i18n.changeLanguage(e.target.value);
                localStorage.setItem('i18nextLng', e.target.value);
              }}
              className="bg-transparent text-gray-300 border-none focus:ring-0 cursor-pointer font-medium text-xs focus:outline-none"
            >
              <option value="en">English</option>
              <option value="tr">Türkçe</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
            </select>
          </div>

          <button
            onClick={async () => {
              await fetch('/api/auth/logout', { method: 'POST' });
              localStorage.removeItem('sentinel_username');
              window.location.href = '/login';
            }}
            className="px-3 py-1.5 bg-red-950/40 hover:bg-red-900/40 text-red-400 border border-red-500/20 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            Log Out
          </button>

          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="font-semibold text-green-400">Live Telemetry</span>
          </div>
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

      {showAuthModal && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-md">
          <div className="bg-[#0d1117] border border-white/10 rounded-xl p-8 max-w-md w-full shadow-2xl animate-in zoom-in duration-200">
            <div className="flex items-center gap-3 mb-6">
              <Key className="w-8 h-8 text-blue-400" />
              <div>
                <h3 className="text-xl font-bold text-white">API Authorization Key</h3>
                <p className="text-xs text-gray-400">SentinelCell gateway is secured.</p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Enter API Secret Key</label>
                <input
                  type="password"
                  placeholder="Enter API_KEY_SECRET"
                  value={modalKeyInput}
                  onChange={(e) => setModalKeyInput(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
              <button
                onClick={handleSaveKey}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-md transition-colors"
              >
                Authenticate Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
