import { useState, useEffect, useCallback, useRef } from 'react';

export const useBroadcaster = (url) => {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [filterType, setFilterType] = useState('ALL'); // ALL, ERROR, HEAL, SECURITY

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
          // Is the HttpOnly cookie insufficient? If an API key is used:
          // token: "..." (optional; the cookie will suffice)
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
    if (filterType === 'ERROR' && log.type && (log.type.includes('FAIL') || log.type.includes('ERROR'))) return true;
    if (filterType === 'HEAL' && log.type && log.type.includes('HEAL')) return true;
    if (filterType === 'SECURITY' && log.type && log.type.includes('SECURITY')) return true;
    return false;
  });

  return { logs: filteredLogs, isConnected, isPaused, filterType, setFilterType, togglePause, clearLogs };
};
