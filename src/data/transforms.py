import torchvision.transforms as T
import torchvision.transforms.functional as TF
import torch
import random


class SequenceTransform:
    """
    Apply the SAME random spatial transform to every frame in a sequence,
    preserving temporal consistency while providing rich augmentation.
    """

    def __init__(self, img_size: int = 224, is_train: bool = True):
        self.img_size = img_size
        self.is_train = is_train
        self.normalize = T.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])

    def __call__(self, frames: list) -> torch.Tensor:
        """frames: list of PIL Images → (T, C, H, W) tensor"""

        # ── Spatial transforms (same params applied to all frames) ──
        resize = T.Resize((self.img_size, self.img_size))
        frames = [resize(f) for f in frames]

        if self.is_train:
            # Random horizontal flip (same for all frames)
            if random.random() > 0.5:
                frames = [TF.hflip(f) for f in frames]

            # Random resized crop (same crop for all frames — temporal consistency)
            if random.random() > 0.3:
                i, j, h, w = T.RandomResizedCrop.get_params(
                    frames[0], scale=(0.75, 1.0), ratio=(0.9, 1.1)
                )
                frames = [TF.resized_crop(f, i, j, h, w, (self.img_size, self.img_size))
                          for f in frames]

            # Color jitter (brightness, contrast, saturation, hue)
            brightness = random.uniform(0.75, 1.25)
            contrast   = random.uniform(0.75, 1.25)
            saturation = random.uniform(0.80, 1.20)
            hue        = random.uniform(-0.05, 0.05)
            frames = [TF.adjust_brightness(f, brightness) for f in frames]
            frames = [TF.adjust_contrast(f, contrast)     for f in frames]
            frames = [TF.adjust_saturation(f, saturation) for f in frames]
            frames = [TF.adjust_hue(f, hue)               for f in frames]

            # Random grayscale (simulates low-light / monochrome cameras)
            if random.random() > 0.85:
                frames = [TF.rgb_to_grayscale(f, num_output_channels=3) for f in frames]

        tensors = [TF.to_tensor(f) for f in frames]
        tensors = [self.normalize(t) for t in tensors]
        return torch.stack(tensors)  # (T, C, H, W)


def get_transforms(img_size: int = 224, is_train: bool = True) -> SequenceTransform:
    return SequenceTransform(img_size=img_size, is_train=is_train)