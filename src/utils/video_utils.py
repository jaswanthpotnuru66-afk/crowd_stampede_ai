import cv2
import numpy as np
from pathlib import Path


def get_video_info(video_path: str) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    info = {
        "fps":          cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width":        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height":       int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration_s":   round(cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1), 2),
    }
    cap.release()
    return info


def read_frames_sampled(video_path: str, sample_rate: int = 5) -> list:
    """Return every Nth frame as list of BGR numpy arrays."""
    cap    = cv2.VideoCapture(str(video_path))
    frames = []
    idx    = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % sample_rate == 0:
            frames.append(frame)
        idx += 1
    cap.release()
    return frames


def open_rtsp(url: str, buffer_size: int = 1) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
    return cap