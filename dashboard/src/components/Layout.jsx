import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Shield, Activity, ShieldAlert, Settings } from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();

  const getTabClass = (path) => {
    const isActive = location.pathname.startsWith(path);
    if (path === '/quarantine') {
      return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-red-500/10 text-red-400' : 'text-gray-400 hover:text-gray-200'}`;
    }
    return `flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${isActive ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'text-gray-400 hover:text-gray-200'}`;
  };

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

      <div className="flex gap-4 mb-8 border-b border-gray-800 pb-2">
        <NavLink to="/dashboard" className={getTabClass('/dashboard')}>
          <Activity className="w-5 h-5" />
          Dashboard
        </NavLink>
        <NavLink to="/settings" className={getTabClass('/settings')}>
          <Settings className="w-5 h-5" />
          Settings
        </NavLink>
        <NavLink to="/quarantine" className={getTabClass('/quarantine')}>
          <ShieldAlert className="w-5 h-5" />
          Quarantine Room
        </NavLink>
      </div>

      <main>
        {children}
      </main>
    </div>
  );
};

export default Layout;
