import React from 'react';
import { Activity, CheckCircle, AlertTriangle, Shield, RefreshCcw, Database, Pause, Play, Trash2, Filter } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useBroadcaster } from '../hooks/useBroadcaster';

const fetchSchemas = async () => {
  const res = await fetch('/api/schemas');
  if (!res.ok) return [];
  const data = await res.json();
  return data.schemas || [];
};

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) return {};
  return res.json();
};

const Dashboard = () => {
  // Use Broadcaster for live tail logs
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const { logs, isConnected, isPaused, filterType, setFilterType, togglePause, clearLogs } = useBroadcaster(`${protocol}//${window.location.host}/ws/logs`);

  const { data: schemas = [] } = useQuery({ queryKey: ['schemas'], queryFn: fetchSchemas, refetchInterval: 10000 });
  const { data: config = {} } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 10000 });

  const metrics = {
    intercepts: logs.length,
    healed: logs.filter(l => l.action === 'healed').length,
    dropped: logs.filter(l => l.action === 'dropped' || l.action === 'quarantined').length,
    quarantineStatus: logs.some(l => l.action === 'quarantined') ? 1 : 0
  };

  return (
    <div className="animate-in fade-in duration-300">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="glass-panel metric-card">
          <Activity className="w-8 h-8 text-blue-400 mb-4" />
          <div className="metric-value text-3xl font-bold">{metrics.intercepts}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Session Packets</div>
        </div>

        <div className="glass-panel metric-card">
          <CheckCircle className="w-8 h-8 text-green-400 mb-4" />
          <div className="metric-value text-3xl font-bold bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">{metrics.healed}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Successfully Healed</div>
        </div>

        <div className="glass-panel metric-card">
          <AlertTriangle className="w-8 h-8 text-yellow-400 mb-4" />
          <div className="metric-value text-3xl font-bold bg-gradient-to-r from-yellow-500 to-yellow-600 bg-clip-text text-transparent">{metrics.dropped}</div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Quarantined / Dropped</div>
        </div>

        <div className={`glass-panel metric-card ${metrics.quarantineStatus ? 'border-red-500/50' : ''}`}>
          <Shield className={`w-8 h-8 mb-4 ${metrics.quarantineStatus ? 'text-red-500 animate-pulse' : 'text-green-400'}`} />
          <div className={`text-2xl font-bold mb-2 ${metrics.quarantineStatus ? 'text-red-500' : 'text-green-400'}`}>
            {metrics.quarantineStatus ? 'QUARANTINE' : 'SAFE'}
          </div>
          <div className="text-sm font-medium text-gray-400 uppercase tracking-wider">Network Status</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-panel p-6 flex flex-col h-96">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Live Tail Logs
              <span className={`px-2 py-0.5 text-xs rounded-full ${isConnected ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
              </span>
            </h2>
            <div className="flex gap-2 items-center">
              <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="bg-black/50 border border-white/10 text-xs text-gray-300 rounded px-2 py-1 focus:outline-none focus:border-blue-500">
                <option value="ALL">All Events</option>
                <option value="HEAL">Heals</option>
                <option value="SECURITY">Security</option>
                <option value="ERROR">Errors</option>
              </select>
              <button onClick={togglePause} className="p-2 hover:bg-white/10 rounded-md transition-colors" title={isPaused ? "Resume" : "Pause"}>
                {isPaused ? <Play className="w-4 h-4 text-green-400" /> : <Pause className="w-4 h-4 text-yellow-400" />}
              </button>
              <button onClick={clearLogs} className="p-2 hover:bg-white/10 rounded-md transition-colors" title="Clear Logs">
                <Trash2 className="w-4 h-4 text-red-400" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto bg-[#0d1117] border border-white/5 rounded-md p-4 font-mono text-xs text-gray-300">
            {logs.length === 0 ? (
              <div className="text-gray-500 italic">Waiting for traffic...</div>
            ) : (
              logs.map((log, i) => {
                let colorClass = "text-gray-300";
                if (log.type?.includes('HEAL_SUCCESS')) colorClass = "text-green-400";
                if (log.type?.includes('HEAL_FAIL')) colorClass = "text-yellow-400";
                if (log.type?.includes('SECURITY')) colorClass = "text-red-400 font-bold";

                return (
                  <div key={i} className="mb-2 pb-2 border-b border-white/5">
                    <span className="text-blue-400">[{log.timestamp.toLocaleTimeString()}]</span>{' '}
                    <span className="text-purple-400 font-bold">[{log.type}]</span>{' '}
                    <span className={colorClass}>{log.content}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Database className="w-5 h-5 text-purple-400" />
            Agnostic Registry
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">FastMCP Schema Server</span>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                CONNECTED ({schemas.length} Schemas)
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">Redis State Sync</span>
              <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                {config.SCHEMA_REGISTRY_PROVIDER === 'REDIS' ? 'ACTIVE (SYNCED)' : 'CONNECTED'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
              <span className="font-mono text-sm text-gray-300">Vector Event Store</span>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-blue-500/30 uppercase">
                ACTIVE ({config.VECTOR_DB_PROVIDER || 'CHROMADB'})
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
