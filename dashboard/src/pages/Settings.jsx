import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, Activity } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { AgentTable } from '../components/AgentTable';

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
};

const Settings = () => {
  const { data: initialConfig, isLoading } = useQuery({ queryKey: ['config'], queryFn: fetchConfig });
  const [config, setConfig] = useState({});
  const [saveMessage, setSaveMessage] = useState("");

  React.useEffect(() => {
    if (initialConfig) setConfig(initialConfig);
  }, [initialConfig]);

  const mutation = useMutation({
    mutationFn: async (newConfig) => {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (!res.ok) throw new Error('Save failed');
      return res.json();
    },
    onSuccess: () => {
      setSaveMessage("Settings saved successfully! (Some changes may require server restart)");
      setTimeout(() => setSaveMessage(""), 5000);
    },
    onError: () => {
      setSaveMessage("Error saving settings.");
      setTimeout(() => setSaveMessage(""), 5000);
    }
  });

  const handleConfigChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  if (isLoading) return <div className="text-center text-gray-400">Loading settings...</div>;

  return (
    <div className="glass-panel p-8 max-w-4xl mx-auto animate-in slide-in-from-bottom-4 duration-300">
      <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
        <SettingsIcon className="w-6 h-6 text-blue-400" />
        Environment Configuration
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">LLM Provider Order</label>
          <input type="text" name="PROVIDER_ORDER" value={config.PROVIDER_ORDER || ""} onChange={handleConfigChange} className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" placeholder="OPENAI,GROQ,LOCAL_OLLAMA" />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">Max Repair Attempts</label>
          <input type="number" name="MAX_REPAIR_ATTEMPTS" value={config.MAX_REPAIR_ATTEMPTS || ""} onChange={handleConfigChange} className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">Quarantine Error Threshold</label>
          <input type="number" name="QUARANTINE_ERROR_THRESHOLD" value={config.QUARANTINE_ERROR_THRESHOLD || ""} onChange={handleConfigChange} className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300 uppercase tracking-wider">LLM Rate Limit (Per Min)</label>
          <input type="number" name="LLM_RATE_LIMIT_PER_MIN" value={config.LLM_RATE_LIMIT_PER_MIN || ""} onChange={handleConfigChange} className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors" />
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
        <span className={`text-sm ${saveMessage.includes('Error') ? 'text-red-400' : 'text-green-400'} font-medium`}>
          {saveMessage}
        </span>
        <button onClick={() => mutation.mutate(config)} disabled={mutation.isPending} className="glow-button flex items-center gap-2 px-6 py-2 disabled:opacity-50">
          <Save className="w-5 h-5" />
          {mutation.isPending ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>

      <div className="mt-12 pt-8 border-t border-white/10">
        <h3 className="text-xl font-semibold mb-6 flex items-center gap-2 text-white">
          <Activity className="w-5 h-5 text-blue-400" />
          Circuit Breakers (Active Agents)
        </h3>
        <AgentTable />
      </div>
    </div>
  );
};

export default Settings;
