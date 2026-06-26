from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def analyze_image_quality(path: str | Path) -> dict[str, Any]:
    """Compute lightweight image quality indicators with OpenCV.

    This is not a full preprocessing pipeline yet. It gives the decision engine
    early signals for blank pages and blurry images.
    """

    file_path = Path(path)
    if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
        return {
            "is_image": False,
            "is_blank": None,
            "blur_score": None,
            "quality_score": None,
            "error": None,
        }

    image = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return {
            "is_image": True,
            "is_blank": None,
            "blur_score": None,
            "quality_score": 0.0,
            "error": "Unable to read image",
        }

    mean = float(np.mean(image))
    std = float(np.std(image))
    blur_score = float(cv2.Laplacian(image, cv2.CV_64F).var())

    # A near-white page with very low variance is considered blank.
    is_blank = mean > 245.0 and std < 5.0

    # Simple bounded quality estimate for POC usage.
    blur_component = min(blur_score / 300.0, 1.0)
    contrast_component = min(std / 64.0, 1.0)
    quality_score = round((0.6 * blur_component) + (0.4 * contrast_component), 3)

    if is_blank:
        quality_score = 0.0

    return {
        "is_image": True,
        "is_blank": bool(is_blank),
        "blur_score": round(blur_score, 3),
        "quality_score": quality_score,
        "error": None,
    }
