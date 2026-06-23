import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, ShieldCheck, AlertTriangle } from 'lucide-react';

const fetchAuditLogs = async () => {
  const res = await fetch('/api/audit-logs');
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
};

const AuditLogs = () => {
  const { data, isLoading } = useQuery({ queryKey: ['auditLogs'], queryFn: fetchAuditLogs, refetchInterval: 10000 });
  const [searchTerm, setSearchTerm] = useState('');

  if (isLoading) return <div className="text-gray-400">Loading audit logs...</div>;

  const logs = data?.logs || [];

  const filteredLogs = logs.filter(log => {
    if (!searchTerm) return true;
    const str = JSON.stringify(log).toLowerCase();
    return str.includes(searchTerm.toLowerCase());
  });

  return (
    <div className="animate-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          OTel Audit Explorer
        </h2>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search by TraceId, schema, or agent..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-black/50 border border-white/10 rounded-md pl-10 pr-4 py-2 text-sm text-white w-80 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="bg-[#0d1117] border border-white/10 rounded-lg overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-gray-500 italic">No audit logs found.</div>
        ) : (
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-900 border-b border-white/10 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">TraceId / SpanId</th>
                <th className="px-4 py-3">Decision ID</th>
                <th className="px-4 py-3">Schema</th>
                <th className="px-4 py-3">LLM Provider</th>
                <th className="px-4 py-3">Result</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log, idx) => (
                <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                  <td className="px-4 py-3 font-mono text-xs">{new Date(log.Timestamp * 1000).toLocaleString()}</td>
                  <td className="px-4 py-3 font-mono text-xs text-blue-400">
                    <div>T: {log.TraceId}</div>
                    <div className="text-gray-500">S: {log.SpanId}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-purple-400">{log.Attributes?.["decision.id"] || "N/A"}</td>
                  <td className="px-4 py-3">{log.Attributes?.["target.schema"] || "Unknown"}</td>
                  <td className="px-4 py-3">{log.Attributes?.["llm.provider"] || "CACHE"}</td>
                  <td className="px-4 py-3">
                    {log.SeverityNumber === 9 ? (
                      <span className="flex items-center gap-1 text-green-400 font-medium bg-green-400/10 px-2 py-1 rounded w-max">
                        <ShieldCheck className="w-4 h-4"/> SUCCESS
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-400 font-medium bg-red-400/10 px-2 py-1 rounded w-max">
                        <AlertTriangle className="w-4 h-4"/> FAIL
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AuditLogs;
