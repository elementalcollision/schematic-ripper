"""Paths and model configuration. No secrets here — the Anthropic key is read
from the environment (ANTHROPIC_API_KEY) by the SDK at call time."""

from __future__ import annotations

import os
from pathlib import Path

# Repo-relative anchors (config.py is at src/schematic_ripper/config.py).
PKG_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_ROOT.parents[1]

SOURCE_IMAGES_DIR = PROJECT_ROOT / "source_images"
SAMPLE_SCHEMATICS_DIR = PROJECT_ROOT / "sample_schematics"
REFERENCES_DIR = PROJECT_ROOT / "data" / "references"
RUNS_DIR = PROJECT_ROOT / "runs"

# Primary multimodal extraction model. Opus for the hard reasoning passes;
# a cheaper tier can be swapped in for bulk per-image OCR.
VISION_MODEL = os.environ.get("SRIPPER_VISION_MODEL", "claude-opus-4-8")
BULK_OCR_MODEL = os.environ.get("SRIPPER_BULK_MODEL", "claude-haiku-4-5-20251001")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".webp"}
