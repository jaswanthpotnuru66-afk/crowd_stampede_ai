from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes_video import router as video_router
from api.routes_live import router as live_router
from api.routes_rtsp import router as rtsp_router

app = FastAPI(title="CrowdSentinel API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router, prefix="/video", tags=["Video Analysis"])
app.include_router(live_router, prefix="/live", tags=["Live Stream"])
app.include_router(rtsp_router, prefix="/rtsp", tags=["RTSP Camera"])


@app.get("/health")
def health():
    return {"status": "ok"}