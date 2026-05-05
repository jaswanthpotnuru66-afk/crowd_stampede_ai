import cv2
import json
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
 
from src.data.pseudo_label_generator import PseudoLabelGenerator
from api.analyzer import analyze_frame_sequence, build_risk_probs
 
router = APIRouter()
 
 
@router.websocket("/ws")
async def webcam_stream(ws: WebSocket):
    """
    Receives raw JPEG frames from browser webcam via WebSocket.
    Returns JSON with risk metrics + density map after each frame.
    """
    await ws.accept()
    gen             = PseudoLabelGenerator()
    density_history = []
 
    try:
        while True:
            data  = await ws.receive_bytes()
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue
 
            result = analyze_frame_sequence([frame], gen, density_history)
 
            payload = {
                **result,
                "risk_probs": build_risk_probs(result["risk_class"]),
                "source": "webcam",
            }
            await ws.send_text(json.dumps(payload))
 
    except WebSocketDisconnect:
        print("Webcam WebSocket disconnected")
    except Exception as e:
        print(f"Webcam WS error: {e}")