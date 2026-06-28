"""End-to-end orchestration: ingest -> vision extraction -> (human confirm) ->
discriminator match -> provenance report.

The confirmation gate is deliberate: vision can mis-read a value, so extracted
BOMs are written to disk for human review and reloaded before they ever drive a
verdict. `analyze()` supports skipping the live API call by passing a prebuilt
BOM (used by tests and by re-runs against a confirmed BOM).
"""

from __future__ import annotations

import json
from pathlib import Path

from . import config, ingest
from .matching import provenance
from .models import BOM, Component, ProvenanceReport
from .reference import loader
from .report import dossier


def extract_bom(images_dir: Path | None = None, model: str | None = None) -> BOM:
    """Run Claude vision over every chassis photo and merge into one BOM."""
    from .vision import claude_extractor

    images_dir = images_dir or config.SOURCE_IMAGES_DIR
    items: list[Component] = []
    for asset in ingest.discover(images_dir=images_dir):
        if asset.kind != "image":
            continue
        items.extend(claude_extractor.extract_components(asset.path, model=model))
    return BOM(source=str(images_dir), items=items)


def save_bom(bom: BOM, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(bom.model_dump_json(indent=2))
    return path


def load_bom(path: Path) -> BOM:
    return BOM.model_validate_json(Path(path).read_text())


def analyze(
    bom: BOM | None = None,
    images_dir: Path | None = None,
    references_dir: Path | None = None,
    model: str | None = None,
) -> ProvenanceReport:
    """Produce a provenance report. If `bom` is given, the vision pass is skipped."""
    if bom is None:
        bom = extract_bom(images_dir=images_dir, model=model)
    signatures = loader.load_all_signatures(references_dir)
    return provenance.assess(bom, signatures)


def write_dossier(report: ProvenanceReport, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or config.RUNS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "provenance_dossier.md"
    out.write_text(dossier.to_markdown(report))
    # also drop the structured report for downstream tooling
    (out_dir / "provenance_report.json").write_text(report.model_dump_json(indent=2))
    return out
