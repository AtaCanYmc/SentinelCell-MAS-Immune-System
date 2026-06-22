import React, { useState, useEffect } from 'react';
import { Shield, Activity, AlertTriangle, CheckCircle, RefreshCcw, Database } from 'lucide-react';
import './index.css';

function App() {
  const [metrics, setMetrics] = useState({
    intercepts: 0,
    healed: 0,
    dropped: 0,
    quarantineStatus: 0
  });

  // Mocking live data fetch. In a real scenario, this would poll /api/metrics from FastAPI
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        intercepts: prev.intercepts + Math.floor(Math.random() * 3),
        healed: prev.healed + (Math.random() > 0.7 ? 1 : 0),
        dropped: prev.dropped + (Math.random() > 0.9 ? 1 : 0),
        quarantineStatus: Math.random() > 0.95 ? 1 : 0
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-8">
      <header className="flex items-center justify-between mb-12">
        <div className="flex items-center gap-4">
          <Shield className="w-12 h-12 text-[#58a6ff]" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight">SentinelCell</h1>
            <p className="text-sm text-gray-400">MAS Immune System - Live Dashboard</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span className="font-semibold text-green-400">System Active</span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="glass-panel metric-card">
          <Activity className="w-8 h-8 text-blue-400 mb-4" />
          <div className="metric-value">{metrics.intercepts}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Total Packets Scanned</div>
        </div>

        <div className="glass-panel metric-card">
          <CheckCircle className="w-8 h-8 text-green-400 mb-4" />
          <div className="metric-value" style={{background: 'linear-gradient(90deg, #3fb950, #2ea043)', WebkitBackgroundClip: 'text'}}>{metrics.healed}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Successfully Healed</div>
        </div>

        <div className="glass-panel metric-card">
          <AlertTriangle className="w-8 h-8 text-yellow-400 mb-4" />
          <div className="metric-value" style={{background: 'linear-gradient(90deg, #d29922, #dbab09)', WebkitBackgroundClip: 'text'}}>{metrics.dropped}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Quarantined / Dropped</div>
        </div>

        <div className="glass-panel metric-card" style={{ borderColor: metrics.quarantineStatus ? 'rgba(218, 54, 51, 0.5)' : '' }}>
          <Shield className={`w-8 h-8 mb-4 ${metrics.quarantineStatus ? 'quarantine-red' : 'text-green-400'}`} />
          <div className={`text-2xl font-bold mb-2 ${metrics.quarantineStatus ? 'text-red-500' : 'text-green-400'}`}>
            {metrics.quarantineStatus ? 'QUARANTINE' : 'SAFE'}
          </div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Network Status</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-panel p-6">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <RefreshCcw className="w-5 h-5 text-blue-400" />
            DLQ Auto-Replay
          </h2>
          <p className="text-gray-400 mb-6 leading-relaxed">
            Dead Letter Queue is currently being managed automatically. Payloads that failed are re-evaluated using exponential backoff without manual intervention.
          </p>
          <button className="glow-button flex items-center gap-2">
            Force Replay Now
          </button>
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Database className="w-5 h-5 text-purple-400" />
            Agnostic Registry
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">FastMCP Schema Server</span>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">CONNECTED</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">Redis State Sync</span>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">SYNCED</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">PGVector Event Store</span>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-blue-500/30">STANDBY</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
