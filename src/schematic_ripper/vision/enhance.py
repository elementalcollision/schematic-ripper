"""Image enhancement for reading faint stamped / inked codes.

Phone photos of stamped serials and ink date-codes are low-contrast, often
rotated, and (on chrome end-bells) mirror-imaged. This crops to the code region
on the FULL-resolution original, upscales, and boosts contrast so the characters
become legible to the vision pass or a human. Pure Pillow — no system deps.

Crop boxes are given as relative ``(x0, y0, x1, y1)`` fractions in 0..1 so they
are independent of the source resolution.
"""

from __future__ import annotations

from pathlib import Path


def enhance(
    src,
    dst,
    box: tuple[float, float, float, float] | None = None,
    scale: int = 4,
    equalize: bool = False,
    invert: bool = False,
    flip_h: bool = False,
    rotate: int = 0,
    threshold: int | None = None,
    sharpen: float = 2.0,
):
    """Produce an enhanced crop suited to OCR/reading. Returns (path, size)."""
    from PIL import Image, ImageFilter, ImageOps

    im = Image.open(src)
    im = ImageOps.exif_transpose(im)  # bake in orientation

    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))

    im = ImageOps.grayscale(im)
    if scale and scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)

    im = ImageOps.autocontrast(im, cutoff=1)
    if equalize:
        im = ImageOps.equalize(im)
    if sharpen:
        im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=int(sharpen * 100), threshold=2))
    if threshold is not None:
        im = im.point(lambda p: 255 if p > threshold else 0)
    if invert:
        im = ImageOps.invert(im)
    if flip_h:
        im = ImageOps.mirror(im)
    if rotate:
        im = im.rotate(rotate, expand=True)

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return str(dst), im.size
