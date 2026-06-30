import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, Activity, Eye, EyeOff, Globe, Search } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { AgentTable } from '../components/AgentTable';

const ConfigInput = ({ configKey, value, onChange }) => {
  const [show, setShow] = useState(false);
  const isSecret = configKey.includes('API_KEY') || configKey.includes('PASSWORD') || configKey.includes('SECRET');

  return (
    <div className="space-y-2">
      <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">{configKey.replace(/_/g, ' ')}</label>
      <div className="relative">
        <input
          type={isSecret && !show ? "password" : "text"}
          name={configKey}
          value={value || ""}
          onChange={onChange}
          className="w-full bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors pr-10"
        />
        {isSecret && (
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
          >
            {show ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
    </div>
  );
};

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
};

const categorizeKey = (key) => {
  if (key.includes('API_KEY')) return 'API Keys';
  if (key.includes('MODEL') || key === 'PROVIDER_ORDER') return 'Models';
  if (key.includes('DB') || key.includes('POSTGRES') || key.includes('PINECONE') || key.includes('SQLITE') || key.includes('SCHEMA')) return 'Database';
  if (key.includes('ELASTICSEARCH') || key.includes('GRAFANA') || key.includes('TELEMETRY')) return 'Observability';
  return 'System';
};

const Settings = () => {
  const { t, i18n } = useTranslation();
  const { data: initialConfig, isLoading } = useQuery({ queryKey: ['config'], queryFn: fetchConfig });
  const [config, setConfig] = useState({});
  const [saveMessage, setSaveMessage] = useState("");
  const [activeTab, setActiveTab] = useState('API Keys');
  const [searchTerm, setSearchTerm] = useState("");

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
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-blue-400" />
          {t('settings.title')}
        </h2>
      </div>

      {(() => {
        const filteredConfig = Object.entries(config).filter(([key]) =>
          key.toLowerCase().replace(/_/g, ' ').includes(searchTerm.toLowerCase())
        );

        const groupedConfig = filteredConfig.reduce((acc, [key, value]) => {
          const category = categorizeKey(key);
          if (!acc[category]) acc[category] = [];
          acc[category].push({ key, value });
          return acc;
        }, {});

        const tabs = Object.keys(groupedConfig).sort();
        const currentTab = tabs.includes(activeTab) ? activeTab : (tabs[0] || '');

        return (
          <>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 mb-6 pb-2">
              <div className="flex space-x-2 overflow-x-auto pb-2 md:pb-0">
                {tabs.map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 rounded-md font-medium text-sm transition-colors whitespace-nowrap ${currentTab === tab ? 'bg-blue-500/20 text-blue-400' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <div className="relative w-full md:w-60">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search settings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-md py-2 pl-9 pr-4 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {groupedConfig[currentTab]?.map(({ key, value }) => (
                <ConfigInput key={key} configKey={key} value={value} onChange={handleConfigChange} />
              ))}
            </div>
          </>
        );
      })()}

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
