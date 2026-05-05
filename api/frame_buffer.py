import threading
from collections import deque
import numpy as np


class FrameBuffer:
    """
    Thread-safe rolling frame buffer.
    Used by both webcam and RTSP routes to maintain
    the last `maxlen` frames for sequence inference.
    """

    def __init__(self, maxlen: int = 8):
        self._buf  = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self.maxlen = maxlen

    def push(self, frame: np.ndarray):
        with self._lock:
            self._buf.append(frame)

    def ready(self) -> bool:
        with self._lock:
            return len(self._buf) == self.maxlen

    def get(self) -> list:
        with self._lock:
            return list(self._buf)

    def clear(self):
        with self._lock:
            self._buf.clear()

    def __len__(self):
        with self._lock:
            return len(self._buf)