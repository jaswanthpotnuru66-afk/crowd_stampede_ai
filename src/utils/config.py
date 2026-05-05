from pathlib import Path

import yaml


def load_config(path: str = "configs/default.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    model_cfg = cfg.setdefault("model", {})
    training_cfg = cfg.get("training") or cfg.get("train") or {}
    cfg["training"] = training_cfg
    cfg["train"] = training_cfg

    data_cfg = cfg.setdefault("data", {})
    paths_cfg = cfg.get("paths") or {}

    data_root = Path(data_cfg.get("root", "data/hajjv2"))
    data_cfg.setdefault("root", str(data_root))
    data_cfg.setdefault("frames_dir", str(data_root / "extracted_frames"))
    data_cfg.setdefault("labels_dir", str(data_root / "pseudo_labels"))
    data_cfg.setdefault("video_dir", str(data_root / "videos"))
    data_cfg.setdefault("train_list", str(data_root / "train_list.txt"))
    data_cfg.setdefault("val_list", str(data_root / "val_list.txt"))
    data_cfg.setdefault("test_list", str(data_root / "test_list.txt"))
    data_cfg.setdefault("img_size", 224)
    data_cfg.setdefault("num_workers", 4)

    seq_len = training_cfg.get("seq_len", data_cfg.get("seq_len", 8))
    data_cfg["seq_len"] = seq_len
    training_cfg["seq_len"] = seq_len

    stride = data_cfg.get("frame_stride", data_cfg.get("stride", 2))
    data_cfg["frame_stride"] = stride
    data_cfg["stride"] = stride
    data_cfg["sample_rate"] = stride

    training_cfg.setdefault("epochs", 50)
    training_cfg.setdefault("batch_size", 4)
    training_cfg.setdefault("lr", 1e-4)
    training_cfg.setdefault("weight_decay", 1e-4)
    training_cfg.setdefault("grad_clip", 1.0)
    training_cfg.setdefault("save_every", 5)

    paths_cfg.setdefault("checkpoints", "checkpoints")
    paths_cfg.setdefault("exports", "exports")
    paths_cfg.setdefault("results", "results")
    paths_cfg.setdefault("logs", "logs")
    cfg["paths"] = paths_cfg

    model_cfg.setdefault("swin_variant", "swin_tiny_patch4_window7_224")
    model_cfg.setdefault("lstm_hidden", 512)
    model_cfg.setdefault("lstm_layers", 2)
    model_cfg.setdefault("num_classes", 3)

    risk_cfg = cfg.setdefault("risk", {})
    risk_cfg.setdefault("label_low_count", 386.0)
    risk_cfg.setdefault("label_high_count", 436.6)
    risk_cfg.setdefault("zone_rows", 2)
    risk_cfg.setdefault("zone_cols", 3)
    risk_cfg.setdefault("zone_min_share", 0.12)
    risk_cfg.setdefault("hotspot_share_moderate", 0.30)
    risk_cfg.setdefault("hotspot_share_high", 0.42)
    risk_cfg.setdefault("zone_growth_moderate", 0.06)
    risk_cfg.setdefault("zone_growth_high", 0.12)
    risk_cfg.setdefault("total_growth_moderate", 0.08)
    risk_cfg.setdefault("total_growth_high", 0.18)
    risk_cfg.setdefault("count_guard_ratio", 0.15)
    risk_cfg.setdefault("distributed_zone_count", 3)
    risk_cfg.setdefault("free_flow_speed", 0.9)
    risk_cfg.setdefault("congestion_speed", 0.45)
    risk_cfg.setdefault("speed_drop_moderate", 0.15)
    risk_cfg.setdefault("speed_drop_high", 0.35)
    risk_cfg.setdefault("turbulence_low", 0.18)

    pseudo_cfg = cfg.setdefault("pseudo_labels", {})
    pseudo_cfg.setdefault("count_mode", "hybrid")
    pseudo_cfg.setdefault("detector_conf", 0.35)
    pseudo_cfg.setdefault("yolo_weight", 0.7)
    pseudo_cfg.setdefault("dense_scene_threshold", 0.14)
    pseudo_cfg.setdefault("min_detector_count", 3)

    return cfg
