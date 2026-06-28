"""Tesseract/OpenCV assist: crop and deskew candidate label regions so the
vision pass (or a human) reads them cleanly. Optional — guarded imports keep the
base install free of OpenCV.

This is an *assist*, never the primary OCR: vintage hand-stamped markings and
busy chassis shots defeat raw Tesseract, but a deskewed, contrast-stretched crop
of a single cap label is often readable.
"""

from __future__ import annotations

from pathlib import Path


def available() -> bool:
    try:
        import cv2  # noqa: F401
        import pytesseract  # noqa: F401
    except Exception:
        return False
    return True


def ocr_region(image_path: Path, bbox: tuple[int, int, int, int]) -> str:
    """OCR a single (x, y, w, h) region after deskew + contrast stretch."""
    import cv2
    import pytesseract

    img = cv2.imread(str(image_path))
    x, y, w, h = bbox
    crop = img[y : y + h, x : x + w]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    return pytesseract.image_to_string(gray).strip()
