"""Discover and normalize input assets.

Builds a registry of the chassis photos and reference documents: stable content
hash, EXIF orientation applied, basic metadata. Orientation matters — several of
the chassis shots are rotated, and the vision pass reads markings far better
right-side-up.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Asset:
    path: Path
    sha256: str
    kind: str               # "image" | "schematic_pdf" | "other"
    width: int | None = None
    height: int | None = None
    meta: dict = field(default_factory=dict)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _image_dims(path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image, ImageOps

        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)  # bake EXIF rotation into pixels
            return im.width, im.height
    except Exception:
        return None, None


def discover(images_dir: Path | None = None, schematics_dir: Path | None = None) -> list[Asset]:
    """Scan the input directories and return a registry of assets."""
    images_dir = images_dir or config.SOURCE_IMAGES_DIR
    schematics_dir = schematics_dir or config.SAMPLE_SCHEMATICS_DIR
    assets: list[Asset] = []

    for p in sorted(images_dir.glob("*")):
        if p.suffix.lower() in config.IMAGE_EXTS:
            w, h = _image_dims(p)
            assets.append(Asset(p, _sha256(p), "image", w, h))

    for p in sorted(schematics_dir.glob("*.pdf")):
        assets.append(Asset(p, _sha256(p), "schematic_pdf"))

    return assets
