import torch


def load_checkpoint_state(checkpoint_path, map_location="cpu") -> dict:
    try:
        checkpoint = torch.load(checkpoint_path, map_location=map_location, weights_only=True)
    except TypeError:
        checkpoint = torch.load(checkpoint_path, map_location=map_location)

    if isinstance(checkpoint, dict):
        for key in ("model", "model_state_dict", "state_dict"):
            if key in checkpoint and isinstance(checkpoint[key], dict):
                checkpoint = checkpoint[key]
                break

    if not isinstance(checkpoint, dict):
        raise TypeError(f"Checkpoint at {checkpoint_path} does not contain a model state dict")

    return {
        key.removeprefix("module."): value
        for key, value in checkpoint.items()
    }


def load_model_weights(model, checkpoint_path, map_location="cpu", strict=True):
    state_dict = load_checkpoint_state(checkpoint_path, map_location=map_location)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        print(f"[checkpoint] WARNING: {len(missing)} missing keys (architecture mismatch?)")
    if unexpected:
        print(f"[checkpoint] WARNING: {len(unexpected)} unexpected keys ignored")
    if strict and (missing or unexpected):
        raise RuntimeError(
            f"Checkpoint architecture mismatch — {len(missing)} missing / "
            f"{len(unexpected)} unexpected keys.\n"
            "Hint: config swin_variant must match the checkpoint's backbone.\n"
            "If retraining with a new backbone, first run: del checkpoints\\*.pth"
        )
    return missing, unexpected
