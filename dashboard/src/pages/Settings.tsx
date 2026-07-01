import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, Activity, Eye, EyeOff, Globe, Search } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { AgentTable } from '../components/AgentTable';
import { fetchWithAuth } from '../hooks/api';
import { Config } from '../types';
import { useToast } from '../components/Toast';

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
  const res = await fetchWithAuth('/api/config');
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
  const toast = useToast();
  const { data: initialConfig, isLoading } = useQuery<Config>({ queryKey: ['config'], queryFn: fetchConfig });
  const [config, setConfig] = useState<Config>({});
  const [saveMessage, setSaveMessage] = useState("");
  const [activeTab, setActiveTab] = useState('API Keys');
  const [searchTerm, setSearchTerm] = useState("");

  const [purgeDays, setPurgeDays] = useState(30);
  const [purgeMessage, setPurgeMessage] = useState("");

  React.useEffect(() => {
    if (initialConfig) setConfig(initialConfig);
  }, [initialConfig]);

  const mutation = useMutation<any, Error, Record<string, any>>({
    mutationFn: async (newConfig) => {
      const res = await fetchWithAuth('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
      if (!res.ok) throw new Error('Save failed');
      return res.json();
    },
    onSuccess: () => {
      toast.success("Settings saved successfully! (Some changes may require server restart)");
      setSaveMessage("Settings saved successfully! (Some changes may require server restart)");
      setTimeout(() => setSaveMessage(""), 5000);
    },
    onError: () => {
      toast.error("Error saving settings.");
      setSaveMessage("Error saving settings.");
      setTimeout(() => setSaveMessage(""), 5000);
    }
  });

  const purgeMutation = useMutation<any, Error, number>({
    mutationFn: async (days) => {
      const res = await fetchWithAuth(`/memory/purge?days=${days}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Purge failed');
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(`Successfully purged ${data.deleted_count} memories older than ${purgeDays} days.`);
      setPurgeMessage(`Successfully purged ${data.deleted_count} memories older than ${purgeDays} days.`);
      setTimeout(() => setPurgeMessage(""), 5000);
    },
    onError: (err) => {
      toast.error(`Purge failed: ${err.message || 'Purge failed'}`);
      setPurgeMessage(`Error: ${err.message || 'Purge failed'}`);
      setTimeout(() => setPurgeMessage(""), 5000);
    }
  });

  const handleConfigChange = (e) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  if (isLoading) return <div className="text-center text-gray-400">Loading settings...</div>;

  return (
    <div className="glass-panel p-8 max-w-5xl mx-auto animate-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-blue-400" />
          {t('settings.title')}
        </h2>
      </div>

      {(() => {
        const filteredConfig = Object.entries(config || {}).filter(([key]) =>
          key.toLowerCase().replace(/_/g, ' ').includes(searchTerm.toLowerCase())
        );

        const groupedConfig = filteredConfig.reduce<Record<string, {key: string, value: any}[]>>((acc, [key, value]) => {
          const category = categorizeKey(key);
          if (!acc[category]) acc[category] = [];
          acc[category].push({ key, value });
          return acc;
        }, {});

        const tabs = [...Object.keys(groupedConfig).sort(), 'System Maintenance'];
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
                    {tab === 'System Maintenance' ? t('settings.system_maintenance') : tab}
                  </button>
                ))}
              </div>
              {currentTab !== 'System Maintenance' && (
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
              )}
            </div>

            {currentTab === 'System Maintenance' ? (
              <div className="bg-black/40 border border-white/10 rounded-lg p-6 mb-8 space-y-6">
                <div>
                  <h4 className="text-lg font-semibold text-white mb-2">{t('settings.garbage_collection')}</h4>
                  <p className="text-sm text-gray-400 mb-4">
                    {t('settings.garbage_desc')}
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 items-end">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">{t('settings.purge_threshold')}</label>
                      <input
                        type="number"
                        min="1"
                        value={purgeDays}
                        onChange={(e) => setPurgeDays(parseInt(e.target.value) || 30)}
                        className="w-24 bg-black/50 border border-white/10 rounded-md p-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                      />
                    </div>
                    <button
                      onClick={() => purgeMutation.mutate(purgeDays)}
                      disabled={purgeMutation.isPending}
                      className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-md font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      {purgeMutation.isPending ? 'Purging...' : t('settings.purge_button')}
                    </button>
                  </div>
                  {purgeMessage && (
                    <div className={`mt-4 p-3 rounded text-sm max-w-md ${purgeMessage.includes('Error') ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}>
                      {purgeMessage}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {groupedConfig[currentTab]?.map(({ key, value }) => (
                  <ConfigInput key={key} configKey={key} value={value} onChange={handleConfigChange} />
                ))}
              </div>
            )}
          </>
        );
      })()}

      {activeTab !== 'System Maintenance' && (
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
          <span className={`text-sm ${saveMessage.includes('Error') ? 'text-red-400' : 'text-green-400'} font-medium`}>
            {saveMessage}
          </span>
          <button onClick={() => mutation.mutate(config)} disabled={mutation.isPending} className="glow-button flex items-center gap-2 px-6 py-2 disabled:opacity-50">
            <Save className="w-5 h-5" />
            {mutation.isPending ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      )}

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
