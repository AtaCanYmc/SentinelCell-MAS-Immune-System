import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Database, FileJson, X, Search, Copy, Check } from 'lucide-react';
import { fetchWithAuth } from '../hooks/api';

export default function SchemaRegistry() {
  const { t } = useTranslation();
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copied, setCopied] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState("");

  const { data: config = {} } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await fetchWithAuth('/api/config');
      if (!res.ok) return {};
      return res.json();
    }
  });

  const { data: schemas, isLoading, isError, refetch } = useQuery({
    queryKey: ['schemas'],
    queryFn: async () => {
      const res = await fetchWithAuth('/api/schemas');
      if (!res.ok) throw new Error('Failed to fetch schemas');
      return res.json();
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const refreshMutation = useMutation({
    mutationFn: async () => {
      const res = await fetchWithAuth('/schema/refresh', {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Refresh failed');
      return res.json();
    },
    onSuccess: () => {
      setRefreshMessage("Schema cache refreshed successfully!");
      refetch();
      setTimeout(() => setRefreshMessage(""), 4000);
    },
    onError: (err) => {
      setRefreshMessage(`Error: ${err.message || 'Refresh failed'}`);
      setTimeout(() => setRefreshMessage(""), 4000);
    }
  });

  const handleCopy = () => {
    if (!selectedSchema) return;
    navigator.clipboard.writeText(JSON.stringify(selectedSchema.schema, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredSchemas = schemas
    ? Object.entries(schemas).filter(
        ([agentId, schema]) =>
          agentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (schema.title || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    : [];

  return (
    <div className="p-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div className="flex items-center">
          <Database className="w-8 h-8 text-[#58a6ff] mr-3" />
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{t('schemas.title')}</h1>
            <p className="text-gray-400 text-sm mt-0.5">{t('schemas.subtitle')}</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap"
          >
            {refreshMutation.isPending ? 'Refreshing...' : t('schemas.refresh_cache')}
          </button>
          {!isLoading && !isError && schemas && Object.keys(schemas).length > 0 && (
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search schemas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/50 border border-white/10 rounded-md py-2 pl-9 pr-4 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          )}
        </div>
      </div>

      {refreshMessage && (
        <div className={`mb-6 p-3 rounded text-sm border ${refreshMessage.includes('Error') ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-green-500/20 text-green-400 border-green-500/30'}`}>
          {refreshMessage}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center p-20 glass-panel">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
        </div>
      ) : isError ? (
        <div className="p-4 bg-red-900/50 text-red-400 rounded-lg border border-red-800">
          Error loading schemas.
        </div>
      ) : !schemas || Object.keys(schemas).length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 bg-gray-800/30 rounded-xl border border-gray-700/50">
          <Database className="w-16 h-16 text-gray-500 mb-4 opacity-50" />
          <p className="text-gray-400 text-lg">{t('schemas.empty')}</p>
        </div>
      ) : filteredSchemas.length === 0 ? (
        <div className="text-center py-20 glass-panel">
          <p className="text-gray-400 text-sm">No matching schemas found.</p>
        </div>
      ) : (
        <div className="overflow-x-auto bg-gray-800/40 rounded-xl border border-gray-700/50 shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-800/80 text-gray-300 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium border-b border-gray-700">{t('schemas.agent_id')}</th>
                <th className="p-4 font-medium border-b border-gray-700">{t('schemas.schema_title')}</th>
                <th className="p-4 font-medium border-b border-gray-700 text-right">{t('schemas.actions')}</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              {filteredSchemas.map(([agentId, schema]) => (
                <tr key={agentId} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                  <td className="p-4 font-mono text-blue-400">{agentId}</td>
                  <td className="p-4">{schema.title || 'Untitled Schema'}</td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => setSelectedSchema({ agentId, schema })}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 hover:text-blue-300 rounded-lg text-sm font-medium transition-all"
                    >
                      <FileJson className="w-4 h-4 mr-2" />
                      {t('schemas.view_details')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {selectedSchema && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
              <div className="flex items-center">
                <FileJson className="w-6 h-6 text-[#58a6ff] mr-2" />
                <h3 className="text-xl font-bold text-gray-100 font-mono">
                  {selectedSchema.agentId}
                </h3>
              </div>
              <button
                onClick={() => setSelectedSchema(null)}
                className="p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 bg-[#090d13] border-b border-gray-800">
              <pre className="text-sm font-mono text-green-400 whitespace-pre-wrap">
                {JSON.stringify(selectedSchema.schema, null, 2)}
              </pre>
            </div>
            <div className="p-4 flex justify-between items-center bg-gray-900/50">
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm font-medium transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-green-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Schema
                  </>
                )}
              </button>
              <button
                onClick={() => setSelectedSchema(null)}
                className="px-4 py-2 bg-[#58a6ff]/10 hover:bg-[#58a6ff]/20 text-[#58a6ff] rounded-lg text-sm font-medium transition-colors"
              >
                {t('schemas.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
