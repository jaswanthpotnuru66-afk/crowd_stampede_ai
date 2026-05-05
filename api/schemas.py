from pydantic import BaseModel
from typing import Optional


class RTSPConnectRequest(BaseModel):
    url: str


class AnalysisResult(BaseModel):
    risk_class:          str
    risk_probs:          list[float]
    count:               int
    count_history:       list[int]
    crowd_coverage:      float
    avg_speed:           float
    velocity_variance:   float
    turbulence:          float
    flow_direction:      str
    density_growth:      str
    high_risk_frame_pct: int
    latency_ms:          int
    frames_analyzed:     int
    zone_risks:          list[str]
    events:              list[dict]
    video_info:          Optional[dict] = None


class LiveFrame(BaseModel):
    risk_class:       str
    risk_probs:       list[float]
    count:            int
    crowd_coverage:   float
    avg_speed:        float
    turbulence:       float
    flow_direction:   str
    density_map_b64:  str
    source:           str