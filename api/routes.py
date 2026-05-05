import asyncio, cv2, base64, time, json, tempfile, os
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse
from .frame_buffer import AsyncFrameBuffer

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Upload a video file and get crowd density predictions for every frame.
    Returns: {"results": [{"frame": N, "timestamp": T, "density": D, "risk_label": R, "turbulence": B}]}
    """
    from .main import inferencer
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        # Process video
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return JSONResponse({"error": "Could not open video"}, status_code=400)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        results = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Preprocess and infer
            processed = inferencer.preprocess(frame)
            inferencer.frame_buffer.append(processed)
            result = inferencer.infer_sequence()
            
            if result:
                timestamp = frame_idx / fps if fps > 0 else 0
                results.append({
                    "frame": frame_idx,
                    "timestamp": round(timestamp, 2),
                    "density": round(result["density"], 2),
                    "risk_label": result["risk_label"],
                    "turbulence": round(result.get("turbulence", 0), 3)
                })
            
            frame_idx += 1
        
        cap.release()
        return {"success": True, "total_frames": frame_idx, "results": results}
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.websocket("/ws/stream")
async def video_stream(websocket: WebSocket):
    """
    Client sends base64 JPEG frames.
    Server responds with inference results as JSON.
    """
    from .main import inferencer, frame_buffer  # avoid circular import
    await websocket.accept()
    t_prev = time.time()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "frame":
                # Decode base64 frame
                img_bytes = base64.b64decode(msg["data"])
                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

                if frame is None:
                    continue

                processed = inferencer.preprocess(frame)
                inferencer.frame_buffer.append(processed)
                result = inferencer.infer_sequence()

                now = time.time()
                fps = 1.0 / max(now - t_prev, 0.001)
                t_prev = now

                if result:
                    result["fps"] = round(fps, 1)
                    await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        pass