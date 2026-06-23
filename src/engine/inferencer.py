import torch
import numpy as np
import cv2
from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
import torchvision.transforms as T


class FastInference:
    """
    Loads a trained CrowdMonitor checkpoint and runs
    FP16 inference on a sequence of frames.
    """
    def __init__(self, checkpoint_path: str, device: str = "cuda"):
        self.device    = device if torch.cuda.is_available() else "cpu"
        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize((224, 224)),
            T.ToTensor(),
        ])
        self.model     = CrowdMonitor().to(self.device)

        load_model_weights(self.model, checkpoint_path, map_location=self.device)
        self.model.eval()

        if self.device == "cuda":
            self.model = self.model.half()

        print(f"FastInference ready on {self.device}")

    @torch.no_grad()
    def predict(self, frames: list) -> dict:
        """
        frames : list of numpy BGR images (len == seq_len)
        returns: dict with risk_class, risk_probs, count
        """
        tensors = []
        for f in frames:
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            t   = self.transform(rgb)
            tensors.append(t)

        seq = torch.stack(tensors).unsqueeze(0).to(self.device)
        if self.device == "cuda":
            seq = seq.half()

        pred_density, risk_logits, turbulence = self.model(seq)

        probs      = torch.softmax(risk_logits, dim=-1)[0].cpu().float().numpy()
        risk_class = ["LOW", "MODERATE", "HIGH"][int(probs.argmax())]
        count      = round(float(pred_density[0].cpu()))

        return {
            "risk_class":  risk_class,
            "risk_probs":  probs.tolist(),
            "count":       count,
            "turbulence":  float(turbulence[0].cpu()),
        }


class VideoStreamInference:
    """
    Maintains a rolling frame buffer and runs inference
    when the buffer is full (seq_len frames).
    Used for both live webcam and RTSP streams.
    """
    def __init__(self, model: FastInference | None, seq_len: int = 8, skip_frames: int = 3):
        self.model       = model
        self.seq_len     = seq_len
        self.skip_frames = skip_frames
        self.buffer: list = []
        self._frame_count = 0

    def push_frame(self, frame: np.ndarray) -> dict | None:
        """
        Push one BGR frame. Returns inference result if buffer is full,
        otherwise returns None.
        """
        self._frame_count += 1
        if self._frame_count % self.skip_frames != 0:
            return None

        self.buffer.append(frame)
        if len(self.buffer) > self.seq_len:
            self.buffer.pop(0)

        if self.buffer_ready():
            return self.infer_from_buffer()
        return None

    def buffer_ready(self) -> bool:
        return len(self.buffer) == self.seq_len

    def infer_from_buffer(self) -> dict:
        if self.model is None:
            return {}
        return self.model.predict(self.buffer)
