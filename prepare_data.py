"""
STEP 1 - Run this first before training.
Extracts frames from all videos and generates pseudo-labels.

Usage:
    python prepare_data.py
"""
import runtime_bootstrap
from pathlib import Path
from src.data.extract_frames import extract_all_videos
from src.data.pseudo_label_generator import generate_dataset_from_videos
from src.utils.config import load_config


def main():
    cfg = load_config()
    data = cfg["data"]

    frames_exist = any(Path(data["frames_dir"]).glob("*.jpg"))
    if frames_exist:
        print("STEP 1a: Frames already exist, skipping extraction.")
    else:
        print("=" * 50)
        print("STEP 1a: Extracting frames from videos")
        print("=" * 50)
        extract_all_videos(
            video_dir=data["video_dir"],
            frames_dir=data["frames_dir"],
            sample_rate=data["sample_rate"],
        )

    print("\n" + "=" * 50)
    print("STEP 1b: Generating pseudo-labels")
    print("=" * 50)
    generate_dataset_from_videos(
        video_dir=data["video_dir"],
        frames_dir=data["frames_dir"],
        labels_dir=data["labels_dir"],
        sample_rate=data["sample_rate"],
        cfg={
            "img_size": data["img_size"],
            **cfg.get("risk", {}),
            **cfg.get("pseudo_labels", {}),
        },
    )

    print("\nData preparation complete.")
    print(f"Frames  -> {data['frames_dir']}")
    print(f"Labels  -> {data['labels_dir']}")
    print("\nNext step: python train.py")


if __name__ == "__main__":
    main()
