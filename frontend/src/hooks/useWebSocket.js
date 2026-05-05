import { useRef, useState, useCallback } from "react";

export default function useWebSocket(url) {
  const wsRef       = useRef(null);
  const timerRef    = useRef(null);
  const videoRef    = useRef(null);
  const streamRef   = useRef(null);
  const [connected, setConnected]   = useState(false);
  const [liveData,  setLiveData]    = useState(null);
  const [error,     setError]       = useState(null);

  const connect = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;

      // Attach stream to a hidden video element for frame capture
      const video = document.createElement("video");
      video.srcObject = stream;
      video.play();
      videoRef.current = video;

      wsRef.current = new WebSocket(url);
      wsRef.current.binaryType = "arraybuffer";

      wsRef.current.onopen = () => {
        setConnected(true);
        setError(null);

        // Send frames at 5 FPS
        const canvas = document.createElement("canvas");
        timerRef.current = setInterval(() => {
          if (wsRef.current?.readyState !== WebSocket.OPEN) return;
          canvas.width  = 640;
          canvas.height = 480;
          canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
          canvas.toBlob(
            (blob) => blob?.arrayBuffer().then((buf) => wsRef.current?.send(buf)),
            "image/jpeg",
            0.8
          );
        }, 200);
      };

      wsRef.current.onmessage = (e) => {
        try {
          setLiveData(JSON.parse(e.data));
        } catch (_) {}
      };

      wsRef.current.onerror = () => setError("WebSocket error");
      wsRef.current.onclose = () => { setConnected(false); };

    } catch (err) {
      setError(`Camera error: ${err.message}`);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    clearInterval(timerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setConnected(false);
    setLiveData(null);
  }, []);

  return { connected, liveData, error, connect, disconnect };
}