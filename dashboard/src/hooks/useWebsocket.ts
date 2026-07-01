import { useState, useEffect, useCallback, useRef } from 'react';

export const useWebsocket = (url) => {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const isPausedRef = useRef(isPaused);
  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    let ws;

    const timer = setTimeout(() => {
      const wsUrl = url.replace(/^http/, 'ws');
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        try {
          const authMsg = {
            type: "AUTH",
            token: localStorage.getItem('sentinel_api_key') || undefined
          };
          ws.send(JSON.stringify(authMsg));
        } catch (e) {
          console.error("Failed to send auth message", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
      };

      ws.onmessage = (event) => {
        if (!isPausedRef.current) {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'AUTH_FAILED') {
              console.warn('WebSocket Auth Failed. Check backend cookie parser.');
              return;
            }
            setLogs((prev) => [data, ...prev].slice(0, 100));
          } catch (e) {
            console.error("Failed to parse websocket message", e);
          }
        }
      };
    }, 100);

    return () => {
      clearTimeout(timer);
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
    };
  }, [url]);

  const togglePause = useCallback(() => setIsPaused((prev) => !prev), []);
  const clearLogs = useCallback(() => setLogs([]), []);

  return { logs, isConnected, isPaused, togglePause, clearLogs };
};
