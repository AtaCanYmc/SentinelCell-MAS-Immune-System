import React, { useState, useEffect } from 'react';
import { Shield, Activity, AlertTriangle, CheckCircle, RefreshCcw, Database, Settings, Save } from 'lucide-react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [metrics, setMetrics] = useState({
    intercepts: 0,
    healed: 0,
    dropped: 0,
    quarantineStatus: 0
  });

  const [config, setConfig] = useState({
    PROVIDER_ORDER: "",
    MAX_REPAIR_ATTEMPTS: "",
    QUARANTINE_ERROR_THRESHOLD: "",
    LLM_RATE_LIMIT_PER_MIN: "",
    PASSIVE_MONITORING: "",
    MCP_FAILURE_POLICY: ""
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  // Fetch initial config
  useEffect(() => {
    if (activeTab === 'settings') {
      fetch('/api/config')
        .then(res => res.json())
        .then(data => setConfig(data))
        .catch(err => console.error("Error fetching config:", err));
    }
  }, [activeTab]);

  // Mocking live data fetch
  useEffect(() => {
    if (activeTab !== 'dashboard') return;
    const interval = setInterval(() => {
      setMetrics(prev => ({
        intercepts: prev.intercepts + Math.floor(Math.random() * 3),
        healed: prev.healed + (Math.random() > 0.7 ? 1 : 0),
        dropped: prev.dropped + (Math.random() > 0.9 ? 1 : 0),
        quarantineStatus: Math.random() > 0.95 ? 1 : 0
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const handleConfigChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  const handleSaveConfig = async () => {
    setIsSaving(true);
    setSaveMessage("");
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        setSaveMessage("Settings saved successfully! (Some changes may require server restart)");
      } else {
        setSaveMessage("Failed to save settings.");
      }
    } catch (err) {
      setSaveMessage("Error saving settings.");
      console.error(err);
    }
    setIsSaving(false);
    setTimeout(() => setSaveMessage(""), 5000);
  };

  return (
    <div className="min-h-screen p-8">
      <header className="flex items-center justify-between mb-8">
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

      <div className="flex gap-4 mb-8 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'dashboard' ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'text-gray-400 hover:text-gray-200'}`}
        >
          <Activity className="w-5 h-5" />
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${activeTab === 'settings' ? 'bg-[#58a6ff]/10 text-[#58a6ff]' : 'text-gray-400 hover:text-gray-200'}`}
        >
          <Settings className="w-5 h-5" />
          Settings
        </button>
      </div>

      {activeTab === 'dashboard' && (
        <>
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
        </>
      )}

      {activeTab === 'settings' && (
        <div className="glass-panel p-8 max-w-4xl mx-auto">
          <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
            <Settings className="w-6 h-6 text-blue-400" />
            Environment Configuration
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">LLM Provider Order</label>
              <input type="text" name="PROVIDER_ORDER" value={config.PROVIDER_ORDER || ""} onChange={handleConfigChange} className="w-full bg-white/5 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" placeholder="OPENAI,GROQ,LOCAL_OLLAMA" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">Max Repair Attempts</label>
              <input type="number" name="MAX_REPAIR_ATTEMPTS" value={config.MAX_REPAIR_ATTEMPTS || ""} onChange={handleConfigChange} className="w-full bg-white/5 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">Quarantine Error Threshold</label>
              <input type="number" name="QUARANTINE_ERROR_THRESHOLD" value={config.QUARANTINE_ERROR_THRESHOLD || ""} onChange={handleConfigChange} className="w-full bg-white/5 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">LLM Rate Limit (Per Min)</label>
              <input type="number" name="LLM_RATE_LIMIT_PER_MIN" value={config.LLM_RATE_LIMIT_PER_MIN || ""} onChange={handleConfigChange} className="w-full bg-white/5 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">MCP Failure Policy</label>
              <select name="MCP_FAILURE_POLICY" value={config.MCP_FAILURE_POLICY || "FAIL_CLOSED"} onChange={handleConfigChange} className="w-full bg-black border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors">
                <option value="FAIL_CLOSED">FAIL_CLOSED</option>
                <option value="FAIL_OPEN">FAIL_OPEN</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">Passive Monitoring</label>
              <select name="PASSIVE_MONITORING" value={config.PASSIVE_MONITORING || "false"} onChange={handleConfigChange} className="w-full bg-black border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors">
                <option value="true">True (Zero Latency Mode)</option>
                <option value="false">False (Inline Protection)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
            <span className={`text-sm ${saveMessage.includes('error') ? 'text-red-400' : 'text-green-400'} font-medium`}>
              {saveMessage}
            </span>
            <button onClick={handleSaveConfig} disabled={isSaving} className="glow-button flex items-center gap-2 px-6 py-2">
              <Save className="w-5 h-5" />
              {isSaving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
