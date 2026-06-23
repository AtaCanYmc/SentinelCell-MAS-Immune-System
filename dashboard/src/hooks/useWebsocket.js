import { useState, useEffect, useCallback } from 'react';

export const useWebsocket = (url) => {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    // Determine the actual WS URL, handling development vs production
    const wsUrl = url.replace(/^http/, 'ws');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      if (!isPaused) {
        try {
          const data = JSON.parse(event.data);
          setLogs((prev) => [data, ...prev].slice(0, 100)); // Keep last 100 logs
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      }
    };

    return () => {
      ws.close();
    };
  }, [url, isPaused]);

  const togglePause = useCallback(() => setIsPaused((prev) => !prev), []);
  const clearLogs = useCallback(() => setLogs([]), []);

  return { logs, isConnected, isPaused, togglePause, clearLogs };
};
