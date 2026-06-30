import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, RefreshCw, CheckCircle2 } from 'lucide-react';

const fetchAgents = async () => {
  const res = await fetch('/api/agents');
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
};

export const AgentTable = () => {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['agents'], queryFn: fetchAgents, refetchInterval: 5000 });

  const resetMutation = useMutation({
    mutationFn: async (agentId) => {
      const res = await fetch(`/api/agents/${agentId}/reset`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to reset');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    }
  });

  if (isLoading) return <div className="text-gray-400">Loading agents...</div>;

  const agents = data?.agents || [];

  if (agents.length === 0) return <div className="text-gray-500 italic">No agents tracked yet.</div>;

  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-lg overflow-hidden">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="bg-gray-900 border-b border-white/10 text-xs uppercase">
          <tr>
            <th className="px-4 py-3">Agent ID</th>
            <th className="px-4 py-3">Errors</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr key={agent.id} className="border-b border-white/5 last:border-0 hover:bg-white/5">
              <td className="px-4 py-3 font-mono text-blue-400">{agent.id}</td>
              <td className="px-4 py-3 font-mono">{agent.errors} / {agent.threshold}</td>
              <td className="px-4 py-3">
                {agent.status === 'HEALTHY' ? (
                  <span className="flex items-center gap-1 text-green-400"><CheckCircle2 className="w-4 h-4"/> Healthy</span>
                ) : (
                  <span className="flex items-center gap-1 text-red-500 font-bold"><ShieldAlert className="w-4 h-4"/> Tripped</span>
                )}
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => resetMutation.mutate(agent.id)}
                  disabled={resetMutation.isPending || agent.status === 'HEALTHY'}
                  className={`flex items-center gap-1 px-3 py-1 rounded text-xs ml-auto transition-colors ${agent.status === 'TRIPPED' ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-800 text-gray-500 cursor-not-allowed'}`}
                >
                  <RefreshCw className={`w-3 h-3 ${resetMutation.isPending ? 'animate-spin' : ''}`} />
                  Reset Breaker
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
