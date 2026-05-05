import cv2
import os
from pathlib import Path
from tqdm import tqdm


def extract_frames(video_path: str, output_dir: str, stride: int = 2):
    """Extract frames from a video at every `stride` frames."""
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    saved = 0

    video_name = Path(video_path).stem
    for i in tqdm(range(total), desc=f"Extracting {video_name}"):
        ret, frame = cap.read()
        if not ret:
            break
        if i % stride == 0:
            out_path = os.path.join(output_dir, f"{video_name}_f{i:06d}.jpg")
            cv2.imwrite(out_path, frame)
            saved += 1

    cap.release()
    print(f"Saved {saved} frames from {video_name} (fps={fps:.1f})")
    return saved


def extract_all_videos(video_dir: str, frames_dir: str, sample_rate: int = 2):
    os.makedirs(frames_dir, exist_ok=True)
    video_paths = sorted(Path(video_dir).glob("*.mp4")) + sorted(Path(video_dir).glob("*.avi"))

    if not video_paths:
        print(f"No videos found in {video_dir}")
        return 0

    total_saved = 0
    for video_path in video_paths:
        total_saved += extract_frames(str(video_path), frames_dir, stride=sample_rate)

    print(f"Extracted {total_saved} frame(s) from {len(video_paths)} video(s)")
    return total_saved
