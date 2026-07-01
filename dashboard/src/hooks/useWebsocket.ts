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
    // Determine the actual WS URL, handling development vs production
    const wsUrl = url.replace(/^http/, 'ws');
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      // First Message Auth: The HttpOnly cookie is sent automatically,
      // and the cookie is verified on the backend.
      // If API_KEY_SECRET is present, the auth message can be sent.
      try {
        const authMsg = {type: "AUTH"};
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
          setLogs((prev) => [data, ...prev].slice(0, 100)); // Keep last 100 logs
        } catch (e) {
          console.error("Failed to parse websocket message", e);
        }
      }
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const togglePause = useCallback(() => setIsPaused((prev) => !prev), []);
  const clearLogs = useCallback(() => setLogs([]), []);

  return { logs, isConnected, isPaused, togglePause, clearLogs };
};
