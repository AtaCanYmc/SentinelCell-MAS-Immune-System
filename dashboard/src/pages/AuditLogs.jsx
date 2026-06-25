import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, ShieldCheck, AlertTriangle } from 'lucide-react';

const fetchAuditLogs = async () => {
  const res = await fetch('/api/audit-logs');
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
};

const AuditLogs = () => {
  const { data, isLoading } = useQuery({ queryKey: ['auditLogs'], queryFn: fetchAuditLogs, refetchInterval: 10000 });
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  if (isLoading) return <div className="text-gray-400">Loading audit logs...</div>;

  const logs = Array.isArray(data?.logs) ? data.logs : [];

  const filteredLogs = logs.filter(log => {
    if (!searchTerm) return true;
    try {
      return JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase());
    } catch {
      return false;
    }
  });

  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / itemsPerPage));
  const currentLogs = filteredLogs.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const getSafeStr = (val) => {
    if (val === null || val === undefined) return "";
    if (typeof val === "object") return JSON.stringify(val);
    return String(val);
  };

  return (
    <div className="animate-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">OTel Audit Explorer</h2>
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            className="bg-black/50 border border-white/10 rounded-md pl-10 pr-4 py-2 text-sm text-white w-80 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="bg-[#0d1117] border border-white/10 rounded-lg overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No logs found.</div>
        ) : (
          <table className="w-full text-left text-sm text-gray-300">
            <thead className="bg-gray-900 border-b border-white/10 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">TraceId / SpanId</th>
                <th className="px-4 py-3">Decision ID</th>
                <th className="px-4 py-3">Result</th>
              </tr>
            </thead>
            <tbody>
              {currentLogs.map((log, idx) => {
                const isLegacy = !log.TraceId;
                let ts = "N/A";
                if (isLegacy && log.timestamp) ts = new Date(log.timestamp).toLocaleString();
                else if (log.Timestamp) ts = new Date(log.Timestamp * 1000).toLocaleString();

                const dId = isLegacy ? log.id : (log.Attributes && log.Attributes["decision.id"]);
                const isSuccess = isLegacy ? !(log.reason || '').includes('Error') : log.SeverityNumber === 9;

                return (
                  <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                    <td className="px-4 py-3 font-mono text-xs">{getSafeStr(ts)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-blue-400">
                      {isLegacy ? "Legacy Log" : `${getSafeStr(log.TraceId)} / ${getSafeStr(log.SpanId)}`}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-purple-400">{getSafeStr(dId)}</td>
                    <td className="px-4 py-3">
                      {isSuccess ? (
                        <span className="text-green-400 font-medium">SUCCESS</span>
                      ) : (
                        <span className="text-red-400 font-medium">FAIL</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 bg-black/40 p-4 rounded-lg border border-white/10">
          <div className="text-sm text-gray-400">
            Page {currentPage} of {totalPages} (Total {filteredLogs.length})
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-md bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white"
            >
              Prev
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 rounded-md bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
