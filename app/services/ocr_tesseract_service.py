from __future__ import annotations

from pathlib import Path

from PIL import Image


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def extract_text(path: str | Path) -> dict:
    """Extract text from a local file.

    For tests and quick POC runs, plain text files are supported without OCR.
    For image files, the service attempts pytesseract. Failures are returned as
    low-confidence OCR results instead of crashing the processing pipeline.
    """

    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return {
            "text": text,
            "confidence": 1.0 if text.strip() else 0.0,
            "word_count": len(text.split()),
            "engine": "plain_text",
            "error": None,
        }

    if suffix in IMAGE_EXTENSIONS:
        try:
            import pytesseract

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="fra+eng")
            return {
                "text": text,
                "confidence": 0.75 if text.strip() else 0.0,
                "word_count": len(text.split()),
                "engine": "tesseract",
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - depends on local OCR binaries
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "engine": "tesseract",
                "error": str(exc),
            }

    return {
        "text": "",
        "confidence": 0.0,
        "word_count": 0,
        "engine": "unsupported",
        "error": f"Unsupported file extension: {suffix}",
    }
