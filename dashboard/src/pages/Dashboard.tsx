import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, Shield, Database, Pause, Play, Trash2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useBroadcaster } from '../hooks/useBroadcaster';
import { fetchWithAuth } from '../hooks/api';
import { WidgetErrorBoundary } from '../App';
import AreaChart from '../components/AreaChart';
import { Metrics } from '../types';
import VirtualList from '../components/VirtualList';

const fetchSchemas = async () => {
  const res = await fetchWithAuth('/api/schemas');
  if (!res.ok) return [];
  const data = await res.json();
  return Object.keys(data || {});
};

const fetchConfig = async () => {
  const res = await fetchWithAuth('/api/config');
  if (!res.ok) return {};
  return res.json();
};

const fetchAuditLogs = async () => {
  const res = await fetchWithAuth('/api/audit-logs');
  if (!res.ok) return { logs: [] };
  return res.json();
};

const fetchMetrics = async (): Promise<Metrics | null> => {
  const res = await fetchWithAuth('/api/metrics');
  if (!res.ok) return null;
  return res.json();
};

let cachedRpsHistory = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
let cachedLatencyHistory = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
let cachedErrorHistory = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

const Dashboard = () => {
  const { t } = useTranslation();
  const { data: config = {} } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 10000 });
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

  // Use Broadcaster for live tail logs, metrics, and hitlAlerts
  const {
    logs,
    isConnected,
    isPaused,
    filterType,
    setFilterType,
    togglePause,
    clearLogs,
    metrics: wsMetrics,
    hitlAlerts
  } = useBroadcaster(`${protocol}//${window.location.host}/ws/logs`);

  const { data: schemas = [] } = useQuery({ queryKey: ['schemas'], queryFn: fetchSchemas, refetchInterval: 10000 });
  const { data: auditData } = useQuery({ queryKey: ['auditLogs'], queryFn: fetchAuditLogs, refetchInterval: 10000 });
  const { data: dlqItems = [] } = useQuery<any[]>({ queryKey: ['dlq'], queryFn: () => fetchWithAuth('/api/dlq').then(res => res.json()), refetchInterval: 5000 });

  // Initial HTTP fetch for metrics, updates handled via WebSocket
  const { data: initialMetrics } = useQuery<Metrics | null>({ queryKey: ['metrics'], queryFn: fetchMetrics });
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  const [rpsHistory, setRpsHistory] = useState(cachedRpsHistory);
  const [latencyHistory, setLatencyHistory] = useState(cachedLatencyHistory);
  const [errorHistory, setErrorHistory] = useState(cachedErrorHistory);
  const [selectedLog, setSelectedLog] = useState<any>(null);

  useEffect(() => {
    if (initialMetrics && !metrics) {
      setMetrics(initialMetrics);
    }
  }, [initialMetrics]);

  useEffect(() => {
    if (wsMetrics) {
      setMetrics(wsMetrics);
    }
  }, [wsMetrics]);

  useEffect(() => {
    if (metrics) {
      const m = metrics as any;
      // RPS
      const currentRps = (m.total_requests_current_min || 0) / 60;
      setRpsHistory((prev) => {
        const next = [...prev.slice(1), currentRps];
        cachedRpsHistory = next;
        return next;
      });

      // Latency
      const currentLatency = m.llm_average_latency_ms || 0;
      setLatencyHistory((prev) => {
        const next = [...prev.slice(1), currentLatency];
        cachedLatencyHistory = next;
        return next;
      });

      // Error Rate
      const totalReq: number = (m.total_requests_current_min as number) || 1;
      const failures: number = m.agent_circuit_breakers
        ? (Object.values(m.agent_circuit_breakers).reduce((acc: number, b: any) => acc + (b.failures || 0), 0) as number)
        : 0;
      const currentErrorRate = (failures / totalReq) * 100;
      setErrorHistory((prev) => {
        const next = [...prev.slice(1), currentErrorRate];
        cachedErrorHistory = next;
        return next;
      });
    }
  }, [metrics]);

  const handleHitlAction = async (approvalId: string, decision: 'APPROVED' | 'REJECTED') => {
    try {
      const res = await fetchWithAuth('/api/hitl/approval', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approval_id: approvalId, decision }),
      });
      if (!res.ok) {
        throw new Error('Action submission failed');
      }
    } catch (err: any) {
      console.error('Failed to submit HITL action:', err.message);
    }
  };

  const [metricScope, setMetricScope] = useState('session'); // 'session' | 'system'

  // Session-based metrics (WS current array)
  const sessionMetrics = {
    intercepts: logs.length,
    healed: logs.filter(l => l.action === 'healed' || l.type?.includes('HEAL_SUCCESS')).length,
    dropped: logs.filter(l => l.action === 'dropped' || l.action === 'quarantined' || l.type?.includes('HEAL_FAIL') || l.type?.includes('SECURITY')).length,
    quarantineStatus: dlqItems.length > 0 ? 1 : (logs.some(l => l.action === 'quarantined' || l.type?.includes('SECURITY')) ? 1 : 0)
  };

  // Database-wide historical totals
  const systemMetrics = {
    intercepts: auditData?.total || 0,
    healed: auditData?.total_healed || 0,
    dropped: (auditData?.total_dropped || 0) + dlqItems.length,
    quarantineStatus: dlqItems.length > 0 ? 1 : 0
  };

  const activeMetrics = metricScope === 'session' ? sessionMetrics : systemMetrics;

  return (
    <div className="animate-in fade-in duration-300">
      {/* HITL Pending Approvals Alert Banner */}
      {hitlAlerts.length > 0 && (
        <div className="mb-6 space-y-3">
          {hitlAlerts.map((alert) => (
            <div
              key={alert.approval_id}
              className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-lg"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500 animate-ping" />
                  <h4 className="text-sm font-bold text-yellow-400 uppercase tracking-wide">
                    Human-in-the-Loop Action Required
                  </h4>
                </div>
                <p className="text-xs text-gray-300 mt-1 leading-relaxed">
                  Agent <span className="font-bold text-white font-mono">{alert.source}</span> transmitted a suspicious payload to <span className="font-bold text-white font-mono">{alert.target}</span>. SentinelCell is waiting for your decision before executing self-healing.
                </p>
                <div className="text-[10px] text-gray-500 font-mono mt-2 uppercase">
                  Approval ID: {alert.approval_id}
                </div>
              </div>

              <div className="flex gap-2 w-full md:w-auto shrink-0">
                <button
                  onClick={() => handleHitlAction(alert.approval_id, 'APPROVED')}
                  className="flex-1 md:flex-none px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-xs font-bold rounded-lg transition-colors shadow-md"
                >
                  Approve Payload
                </button>
                <button
                  onClick={() => handleHitlAction(alert.approval_id, 'REJECTED')}
                  className="flex-1 md:flex-none px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg transition-colors shadow-md"
                >
                  Drop Packet
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Metric Scope Selector */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex bg-black/40 p-1 rounded-lg border border-white/10 text-xs">
          <button
            onClick={() => setMetricScope('session')}
            className={`px-3 py-1.5 rounded font-bold transition-all ${
              metricScope === 'session'
                ? 'bg-[#58a6ff]/10 text-[#58a6ff]'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t('dashboard.session_view')}
          </button>
          <button
            onClick={() => setMetricScope('system')}
            className={`px-3 py-1.5 rounded font-bold transition-all ${
              metricScope === 'system'
                ? 'bg-[#58a6ff]/10 text-[#58a6ff]'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t('dashboard.system_totals')}
          </button>
        </div>
        <div className="text-xs text-gray-500 font-mono">
          {t('dashboard.scope')}: {metricScope === 'session' ? t('dashboard.live_browser_session') : t('dashboard.historical_audit_log')}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="glass-panel metric-card">
          <Activity className="w-8 h-8 text-blue-400 mb-4" />
          <div className="metric-value text-3xl font-bold">{activeMetrics.intercepts}</div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-1">
            {metricScope === 'session' ? t('dashboard.session_packets') : t('dashboard.total_intercepted')}
          </div>
        </div>

        <div className="glass-panel metric-card">
          <CheckCircle className="w-8 h-8 text-green-400 mb-4" />
          <div className="metric-value text-3xl font-bold bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">
            {activeMetrics.healed}
          </div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-1">{t('dashboard.successfully_healed')}</div>
        </div>

        <div className="glass-panel metric-card">
          <AlertTriangle className="w-8 h-8 text-yellow-400 mb-4" />
          <div className="metric-value text-3xl font-bold bg-gradient-to-r from-yellow-500 to-yellow-600 bg-clip-text text-transparent">
            {activeMetrics.dropped}
          </div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-1">{t('dashboard.quarantined_dropped')}</div>
        </div>

        <div className={`glass-panel metric-card ${activeMetrics.quarantineStatus ? 'border-red-500/50' : ''}`}>
          <Shield className={`w-8 h-8 mb-4 ${activeMetrics.quarantineStatus ? 'text-red-500 animate-pulse' : 'text-green-400'}`} />
          <div className={`text-2xl font-bold mb-2 ${activeMetrics.quarantineStatus ? 'text-red-500' : 'text-green-400'}`}>
            {activeMetrics.quarantineStatus ? t('dashboard.quarantine') : t('dashboard.safe')}
          </div>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{t('dashboard.network_status')}</div>
        </div>
      </div>

      {/* Live Metrics SVG Charts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="glass-panel p-4">
          <WidgetErrorBoundary title={t('dashboard.requests_per_second')}>
            <AreaChart data={rpsHistory} label={t('dashboard.requests_per_second')} color="#3b82f6" height={100} />
          </WidgetErrorBoundary>
        </div>
        <div className="glass-panel p-4">
          <WidgetErrorBoundary title={t('dashboard.llm_average_latency')}>
            <AreaChart data={latencyHistory} label={t('dashboard.llm_average_latency')} color="#a855f7" height={100} />
          </WidgetErrorBoundary>
        </div>
        <div className="glass-panel p-4">
          <WidgetErrorBoundary title={t('dashboard.active_error_rate')}>
            <AreaChart data={errorHistory} label={t('dashboard.active_error_rate')} color="#ef4444" height={100} />
          </WidgetErrorBoundary>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass-panel p-6 flex flex-col h-96">
          <WidgetErrorBoundary title={t('dashboard.live_tail_logs')}>
            <div className="flex flex-col h-full w-full">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  {t('dashboard.live_tail_logs')}
                  <span className={`px-2 py-0.5 text-xs rounded-full ${isConnected ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                    {isConnected ? t('dashboard.connected') : t('dashboard.disconnected')}
                  </span>
                </h2>
                <div className="flex gap-2 items-center">
                  <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="bg-black/50 border border-white/10 text-xs text-gray-300 rounded px-2 py-1 focus:outline-none focus:border-blue-500">
                    <option value="ALL">{t('dashboard.all_events')}</option>
                    <option value="HEAL">{t('dashboard.heals')}</option>
                    <option value="SECURITY">{t('dashboard.security')}</option>
                    <option value="ERROR">{t('dashboard.errors')}</option>
                  </select>
                  <button onClick={togglePause} className="p-2 hover:bg-white/10 rounded-md transition-colors" title={isPaused ? "Resume" : "Pause"}>
                    {isPaused ? <Play className="w-4 h-4 text-green-400" /> : <Pause className="w-4 h-4 text-yellow-400" />}
                  </button>
                  <button onClick={clearLogs} className="p-2 hover:bg-white/10 rounded-md transition-colors" title="Clear Logs">
                    <Trash2 className="w-4 h-4 text-red-400" />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto bg-[#0d1117] border border-white/5 rounded-md p-4 font-mono text-xs text-gray-300">
                {logs.length === 0 ? (
                  <div className="text-gray-500 italic">{t('dashboard.waiting_for_traffic')}</div>
                ) : (
                  <VirtualList
                    items={logs}
                    rowHeight={34}
                    renderItem={(log: any) => {
                      let colorClass = 'text-gray-300';
                      if (log.type?.includes('HEAL_SUCCESS')) colorClass = 'text-green-400';
                      if (log.type?.includes('HEAL_FAIL')) colorClass = 'text-yellow-400';
                      if (log.type?.includes('SECURITY')) colorClass = 'text-red-400 font-bold';

                      return (
                        <div
                          onClick={() => setSelectedLog(log)}
                          className="mb-2 pb-2 border-b border-white/5 cursor-pointer hover:bg-white/5 transition-colors truncate whitespace-nowrap overflow-hidden text-ellipsis flex items-center gap-2"
                          style={{ height: '34px', boxSizing: 'border-box' }}
                        >
                          <span className="text-blue-400 font-mono shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                          <span className="text-purple-400 font-bold font-mono shrink-0">[{log.type}]</span>{' '}
                          <span className={`${colorClass} truncate text-ellipsis`}>{log.content}</span>
                        </div>
                      );
                    }}
                  />
                )}
              </div>
            </div>
          </WidgetErrorBoundary>
        </div>

        <div className="glass-panel p-6">
          <WidgetErrorBoundary title={t('dashboard.agnostic_registry')}>
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-400" />
              {t('dashboard.agnostic_registry')}
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
                <span className="font-mono text-sm text-gray-300">{t('dashboard.fastmcp_schema_server')}</span>
                <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                  {t('dashboard.connected')} ({schemas.length} Schemas)
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
                <span className="font-mono text-sm text-gray-300">{t('dashboard.redis_state_sync')}</span>
                <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                  {config.SCHEMA_REGISTRY_PROVIDER === 'REDIS' ? 'ACTIVE (SYNCED)' : t('dashboard.connected')}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg border border-white/10">
                <span className="font-mono text-sm text-gray-300">{t('dashboard.vector_event_store')}</span>
                <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-green-500/30 uppercase">
                  ACTIVE ({config.VECTOR_DB_PROVIDER || 'CHROMADB'})
                </span>
              </div>
            </div>
          </WidgetErrorBoundary>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 font-sans">
          <div className="bg-[#0d1117] border border-white/10 rounded-xl p-6 max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase">
                    {selectedLog.type}
                  </span>
                  <span>Event Details</span>
                </h3>
                <p className="text-xs text-gray-400 mt-1 font-mono">
                  {new Date(selectedLog.timestamp).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-white transition-colors text-sm font-bold bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-md cursor-pointer"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              {(selectedLog.source || selectedLog.target) && (
                <div className="grid grid-cols-2 gap-4 bg-black/45 p-3 rounded-lg border border-white/5 text-xs font-mono">
                  <div>
                    <span className="text-gray-500 block mb-1 uppercase tracking-wider text-[10px]">Source Agent</span>
                    <span className="text-blue-400 font-bold">{selectedLog.source || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block mb-1 uppercase tracking-wider text-[10px]">Target Agent</span>
                    <span className="text-purple-400 font-bold">{selectedLog.target || 'N/A'}</span>
                  </div>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Log Content</label>
                <div className="bg-black/60 border border-white/5 rounded-lg p-4 text-xs font-mono text-gray-300 break-words whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                  {selectedLog.content}
                </div>
              </div>

              <TraceTimeline log={selectedLog} />

              {selectedLog.approval_id && (
                <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-lg flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-yellow-400 block uppercase">HITL Verification Pending</span>
                    <span className="text-[11px] text-gray-400">Approval ID: {selectedLog.approval_id}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        handleHitlAction(selectedLog.approval_id, 'APPROVED');
                        setSelectedLog(null);
                      }}
                      className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white font-medium text-xs rounded transition-colors cursor-pointer"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        handleHitlAction(selectedLog.approval_id, 'REJECTED');
                        setSelectedLog(null);
                      }}
                      className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white font-medium text-xs rounded transition-colors cursor-pointer"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const TraceTimeline = ({ log }: { log: any }) => {
  if (!log) return null;

  const isHealed = log.type?.includes('HEAL_SUCCESS') || log.type?.includes('HEAL') || log.content?.includes('Fixed') || log.content?.includes('Healed');
  const isSecurity = log.type?.includes('SECURITY') || log.content?.includes('SECURITY') || log.content?.includes('POISONING');

  const spans = [
    { name: 'Gateway Intercept (validate)', duration: 12, start: 0, color: 'bg-blue-500' },
    ...(isSecurity ? [
      { name: 'Sanitization Check (security_sanitizer)', duration: 8, start: 12, color: 'bg-red-500 animate-pulse' },
      { name: 'Packet Quarantine Alert (dlq_lpush)', duration: 5, start: 20, color: 'bg-rose-600' }
    ] : isHealed ? [
      { name: 'LLM Self-Healing (llm_inference)', duration: 1140, start: 12, color: 'bg-purple-500 animate-pulse' },
      { name: 'Semantic Jaccard Guard (drift_check)', duration: 32, start: 1152, color: 'bg-indigo-500' },
      { name: 'Outbox Event Async Log (sentinel.outbox)', duration: 6, start: 1184, color: 'bg-emerald-500' }
    ] : [
      { name: 'Pass-through Schema Validation', duration: 4, start: 12, color: 'bg-green-500' }
    ])
  ];

  const totalDuration = spans.reduce((acc, s) => Math.max(acc, s.start + s.duration), 0);

  return (
    <div className="bg-black/50 p-4 rounded-lg border border-white/5 space-y-3 mt-4">
      <div className="flex justify-between items-center">
        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Distributed Trace Timeline</h4>
        <span className="text-[10px] font-mono text-gray-500">Trace ID: {log.TraceId || 'system-local'}</span>
      </div>
      <div className="space-y-3 font-mono text-[10px]">
        {spans.map((span, idx) => {
          const leftPercent = (span.start / totalDuration) * 100;
          const widthPercent = (span.duration / totalDuration) * 100;

          return (
            <div key={idx} className="flex items-center gap-4">
              <div className="w-52 text-gray-300 truncate font-semibold" title={span.name}>
                {span.name}
              </div>
              <div className="flex-1 bg-white/5 h-4 rounded relative overflow-hidden">
                <div
                  className={`absolute top-0 bottom-0 rounded ${span.color}`}
                  style={{
                    left: `${leftPercent}%`,
                    width: `${Math.max(widthPercent, 1.5)}%`
                  }}
                />
                <span className="absolute right-2 top-0.5 text-[8px] text-gray-400">
                  {span.duration}ms
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-[8px] text-gray-500 pt-1 border-t border-white/5 font-mono">
        <span>0ms</span>
        <span>{totalDuration}ms (Total Latency)</span>
      </div>
    </div>
  );
};

export default Dashboard;
