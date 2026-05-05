import { useRef, useState, useCallback } from "react";

const API = "http://localhost:8000";
const WS  = "ws://localhost:8000";

export default function useRTSP() {
  const wsRef    = useRef(null);
  const [connected,  setConnected]  = useState(false);
  const [liveData,   setLiveData]   = useState(null);
  const [error,      setError]      = useState(null);
  const [rtspUrl,    setRtspUrl]    = useState("");

  const connect = useCallback(async (url) => {
    setError(null);
    try {
      // Tell backend to open the RTSP stream
      const res = await fetch(`${API}/rtsp/connect`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ url }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Connection failed");
      }

      // Subscribe to results via WebSocket
      wsRef.current = new WebSocket(`${WS}/rtsp/ws`);
      wsRef.current.onopen    = () => setConnected(true);
      wsRef.current.onmessage = (e) => {
        try { setLiveData(JSON.parse(e.data)); } catch (_) {}
      };
      wsRef.current.onerror = () => setError("Lost connection to server");
      wsRef.current.onclose = () => setConnected(false);

    } catch (err) {
      setError(err.message);
    }
  }, []);

  const disconnect = useCallback(async () => {
    wsRef.current?.close();
    wsRef.current = null;
    await fetch(`${API}/rtsp/disconnect`, { method: "POST" });
    setConnected(false);
    setLiveData(null);
  }, []);

  return { connected, liveData, error, rtspUrl, setRtspUrl, connect, disconnect };
}