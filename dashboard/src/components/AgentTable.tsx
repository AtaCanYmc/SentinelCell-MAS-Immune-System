import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, RefreshCw, CheckCircle2 } from 'lucide-react';
import { fetchWithAuth } from '../hooks/api';
import { useToast } from './Toast';

const fetchAgents = async () => {
  const res = await fetchWithAuth('/api/agents');
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
};

const StatusCell = ({ agent }: { agent: any }) => {
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    if (agent.status === 'TRIPPED' && agent.last_failure_time && agent.cooldown) {
      const calculateTimeLeft = () => {
        const elapsed = Date.now() / 1000 - agent.last_failure_time;
        const remaining = Math.max(0, Math.ceil(agent.cooldown - elapsed));
        setSecondsLeft(remaining);
      };

      calculateTimeLeft();
      const timer = setInterval(calculateTimeLeft, 1000);
      return () => clearInterval(timer);
    } else {
      setSecondsLeft(0);
    }
  }, [agent]);

  if (agent.status === 'HEALTHY') {
    return <span className="flex items-center gap-1 text-green-400"><CheckCircle2 className="w-4 h-4"/> Healthy</span>;
  }

  if (agent.status === 'RECOVERING') {
    return <span className="flex items-center gap-1 text-yellow-500 font-bold animate-pulse"><RefreshCw className="w-4 h-4"/> Half-Open (Recovering)</span>;
  }

  return (
    <div className="flex flex-col gap-0.5">
      <span className="flex items-center gap-1 text-red-500 font-bold"><ShieldAlert className="w-4 h-4"/> Tripped</span>
      {secondsLeft > 0 && (
        <span className="text-[10px] text-gray-500 font-mono">Reset in: {secondsLeft}s</span>
      )}
    </div>
  );
};

export const AgentTable = () => {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data, isLoading } = useQuery({ queryKey: ['agents'], queryFn: fetchAgents, refetchInterval: 5000 });

  const resetMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const res = await fetchWithAuth(`/api/agents/${agentId}/reset`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to reset');
      return res.json();
    },
    onSuccess: (_, agentId) => {
      toast.success(`Agent ${agentId} circuit breaker successfully reset.`);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
    onError: (err) => {
      toast.error(err.message || 'Failed to reset agent breaker.');
    }
  });

  if (isLoading) return <div className="text-gray-400">Loading agents...</div>;

  const agents = data?.agents || [];

  if (agents.length === 0) return <div className="text-gray-500 italic">No agents tracked yet.</div>;

  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-lg overflow-hidden overflow-x-auto">
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
              <td className="px-4 py-3 font-mono">{typeof agent.errors === 'object' && agent.errors !== null ? agent.errors.failures : agent.errors} / {agent.threshold}</td>
              <td className="px-4 py-3">
                <StatusCell agent={agent} />
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
