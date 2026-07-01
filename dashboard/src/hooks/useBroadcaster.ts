import { useState, useEffect, useCallback, useRef } from 'react';

export const useBroadcaster = (url) => {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [filterType, setFilterType] = useState('ALL'); // ALL, ERROR, HEAL, SECURITY
  const [metrics, setMetrics] = useState<any>(null);
  const [hitlAlerts, setHitlAlerts] = useState<any[]>([]);

  const isPausedRef = useRef(isPaused);
  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    const wsUrl = url.replace(/^http/, 'ws');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      try {
        const authMsg = {
          type: "AUTH",
          token: window.localStorage.getItem('sentinel_api_key') || undefined,
        };
        ws.send(JSON.stringify(authMsg));
      } catch (e) {
        console.error("Failed to send auth message", e);
      }
      setIsConnected(true);
    };
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      if (!isPausedRef.current) {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'AUTH_FAILED') {
            console.error('WebSocket authentication failed');
            ws.close();
            return;
          }
          if (data.type === 'METRICS') {
            try {
              const parsedMetrics = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
              setMetrics(parsedMetrics);
            } catch (err) {
              console.error('Failed to parse metrics content', err);
            }
            return;
          }
          if (data.type === 'HITL_APPROVAL_REQUIRED') {
            setHitlAlerts((prev) => {
              if (prev.some(alert => alert.approval_id === data.approval_id)) return prev;
              return [...prev, data];
            });
            setLogs((prev) => [{ ...data, content: `HITL Approval Required for agent: ${data.source}`, timestamp: new Date() }, ...prev].slice(0, 1000));
            return;
          }
          if (data.type === 'HITL_DECISION') {
            setHitlAlerts((prev) => prev.filter(alert => alert.approval_id !== data.approval_id));
            setLogs((prev) => [{ ...data, content: `HITL Decision for ${data.approval_id}: ${data.decision}`, timestamp: new Date() }, ...prev].slice(0, 1000));
            return;
          }
          // Keep an in-memory cap to prevent DOM bloat and OOM during high-throughput
          // log bursts. This cap is intentionally generous (1000) and will be
          // rendered with a virtualized list on the Dashboard.
          setLogs((prev) => [{ ...data, timestamp: new Date() }, ...prev].slice(0, 1000));
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      }
    };

    return () => ws.close();
  }, [url]);

  const togglePause = useCallback(() => setIsPaused((prev) => !prev), []);
  const clearLogs = useCallback(() => setLogs([]), []);

  const filteredLogs = logs.filter(log => {
    if (filterType === 'ALL') return true;
    if (filterType === 'ERROR' && log.type && (log.type.includes('FAIL') || log.type.includes('ERROR') || log.type.includes('SYSTEM_ERROR'))) return true;
    if (filterType === 'HEAL' && log.type && log.type.includes('HEAL')) return true;
    if (filterType === 'SECURITY' && log.type && log.type.includes('SECURITY')) return true;
    return false;
  });

  return { logs: filteredLogs, isConnected, isPaused, filterType, setFilterType, togglePause, clearLogs, metrics, hitlAlerts, setHitlAlerts };
};
