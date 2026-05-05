import cv2
import json
import asyncio
import threading
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.data.pseudo_label_generator import PseudoLabelGenerator
from api.analyzer import analyze_frame_sequence, build_risk_probs

router = APIRouter()

# ── Global RTSP state ──────────────────────────────────────────────────────
_rtsp_state = {
    "url":       None,
    "cap":       None,
    "running":   False,
    "connected": False,
    "latest":    None,          # latest result dict
    "error":     None,
}
_ws_clients: list[WebSocket] = []
_state_lock = threading.Lock()


# ── Pydantic models ────────────────────────────────────────────────────────
class RTSPConnectRequest(BaseModel):
    url: str                    # e.g. rtsp://admin:pass@192.168.1.100:554/stream


# ── REST: connect to RTSP ─────────────────────────────────────────────────
@router.post("/connect")
def connect_rtsp(req: RTSPConnectRequest):
    with _state_lock:
        if _rtsp_state["running"]:
            _stop_rtsp()

        cap = cv2.VideoCapture(req.url, cv2.CAP_FFMPEG)
        # Set buffer size small so we always get latest frame
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            raise HTTPException(status_code=400, detail=f"Cannot connect to RTSP: {req.url}")

        _rtsp_state["url"]       = req.url
        _rtsp_state["cap"]       = cap
        _rtsp_state["running"]   = True
        _rtsp_state["connected"] = True
        _rtsp_state["error"]     = None

    t = threading.Thread(target=_rtsp_read_loop, daemon=True)
    t.start()

    return JSONResponse({"status": "connected", "url": req.url})


# ── REST: disconnect RTSP ─────────────────────────────────────────────────
@router.post("/disconnect")
def disconnect_rtsp():
    with _state_lock:
        _stop_rtsp()
    return JSONResponse({"status": "disconnected"})


# ── REST: current RTSP status ─────────────────────────────────────────────
@router.get("/status")
def rtsp_status():
    return {
        "connected": _rtsp_state["connected"],
        "url":       _rtsp_state["url"],
        "error":     _rtsp_state["error"],
    }


# ── WebSocket: stream RTSP results to browser ─────────────────────────────
@router.websocket("/ws")
async def rtsp_ws(ws: WebSocket):
    """
    Browser connects here to receive live RTSP analysis results.
    No frames are sent from browser — results come from server-side RTSP reader.
    """
    await ws.accept()
    _ws_clients.append(ws)
    try:
        while True:
            await asyncio.sleep(0.2)   # keep connection alive
            if _rtsp_state["latest"]:
                await ws.send_text(json.dumps(_rtsp_state["latest"]))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"RTSP WS error: {e}")
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


# ── Background thread: read RTSP + analyze ────────────────────────────────
def _rtsp_read_loop():
    gen             = PseudoLabelGenerator()
    density_history = []
    frame_count     = 0

    while _rtsp_state["running"]:
        cap = _rtsp_state["cap"]
        if cap is None:
            break

        ret, frame = cap.read()
        if not ret:
            with _state_lock:
                _rtsp_state["connected"] = False
                _rtsp_state["error"]     = "Stream lost — attempting reconnect"
            _attempt_reconnect()
            continue

        # Analyze every 3rd frame for speed
        if frame_count % 3 == 0:
            result = analyze_frame_sequence([frame], gen, density_history)
            if result:
                payload = {
                    **result,
                    "risk_probs": build_risk_probs(result["risk_class"]),
                    "source": "rtsp",
                    "url": _rtsp_state["url"],
                }
                with _state_lock:
                    _rtsp_state["latest"] = payload

        frame_count += 1

    print("RTSP read loop ended")


def _attempt_reconnect(max_tries: int = 5):
    import time
    url = _rtsp_state["url"]
    if not url:
        return

    for attempt in range(max_tries):
        time.sleep(3)
        print(f"Reconnect attempt {attempt + 1}/{max_tries} → {url}")
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if cap.isOpened():
            with _state_lock:
                _rtsp_state["cap"]       = cap
                _rtsp_state["connected"] = True
                _rtsp_state["error"]     = None
            print("Reconnected successfully")
            return
        cap.release()

    with _state_lock:
        _rtsp_state["running"]   = False
        _rtsp_state["connected"] = False
        _rtsp_state["error"]     = "Reconnect failed after 5 attempts"
    print("RTSP reconnect failed")


def _stop_rtsp():
    _rtsp_state["running"]   = False
    _rtsp_state["connected"] = False
    if _rtsp_state["cap"]:
        _rtsp_state["cap"].release()
        _rtsp_state["cap"] = None
    _rtsp_state["latest"] = None