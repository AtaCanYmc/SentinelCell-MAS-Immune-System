import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Database, FileJson, X } from 'lucide-react';

export default function SchemaRegistry() {
  const { t } = useTranslation();
  const [selectedSchema, setSelectedSchema] = useState(null);

  const { data: schemas, isLoading, isError } = useQuery({
    queryKey: ['schemas'],
    queryFn: async () => {
      const res = await fetch('/api/schemas');
      if (!res.ok) throw new Error('Failed to fetch schemas');
      return res.json();
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  return (
    <div className="p-6">
      <div className="flex items-center mb-6">
        <Database className="w-8 h-8 text-blue-400 mr-3" />
        <div>
          <h1 className="text-2xl font-bold text-gray-100">{t('schemas.title')}</h1>
          <p className="text-gray-400">{t('schemas.subtitle')}</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-8">
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
              {Object.entries(schemas).map(([agentId, schema]) => (
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
              <div className="flex items-center">
                <FileJson className="w-6 h-6 text-blue-400 mr-2" />
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
            <div className="p-4 overflow-y-auto flex-1 bg-[#1e1e1e]">
              <pre className="text-sm font-mono text-green-400 whitespace-pre-wrap">
                {JSON.stringify(selectedSchema.schema, null, 2)}
              </pre>
            </div>
            <div className="p-4 border-t border-gray-800 flex justify-end">
              <button
                onClick={() => setSelectedSchema(null)}
                className="px-4 py-2 bg-gray-800 text-gray-200 hover:bg-gray-700 rounded-lg transition-colors font-medium"
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
