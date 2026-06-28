"""Enhancement crops + scales as specified (no external image needed)."""

from PIL import Image

from schematic_ripper.vision import enhance


def test_enhance_crop_and_scale(tmp_path):
    src = tmp_path / "in.png"
    Image.new("RGB", (100, 80), (120, 120, 120)).save(src)
    dst = tmp_path / "out.png"

    _, size = enhance.enhance(src, dst, box=(0.0, 0.0, 0.5, 0.5), scale=2)

    assert dst.exists()
    # crop to 50x40, then 2x -> 100x80
    assert size == (100, 80)


def test_enhance_rotate_swaps_dims(tmp_path):
    src = tmp_path / "in.png"
    Image.new("L", (60, 30), 128).save(src)
    dst = tmp_path / "out.png"

    _, size = enhance.enhance(src, dst, scale=1, rotate=90)

    assert size == (30, 60)
