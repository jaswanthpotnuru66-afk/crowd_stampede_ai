from pathlib import Path
from src.engine.inferencer import FastInference
 
_MODEL = None
 
 
def get_model() -> FastInference | None:
    global _MODEL
    if _MODEL is None:
        candidates = [Path("checkpoints/best.pth"), Path("checkpoints/best_model.pth")]
        ckpt = next((path for path in candidates if path.exists()), None)
        if ckpt is not None:
            _MODEL = FastInference(str(ckpt))
            print(f"Model loaded from {ckpt}")
        else:
            print("WARNING: No checkpoint found. Using pseudo-label-only mode.")
    return _MODEL
