"""Load and validate the YAML reference fixtures into typed models.

Reference circuits are authored by a human once (vision-assisted transcription of
the hand-drawn Fender documents), then frozen here as version-controlled ground
truth. The matcher trusts these absolutely, so they are validated on load.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .. import config
from ..models import CircuitSignature


def load_signature(path: Path) -> CircuitSignature:
    data = yaml.safe_load(path.read_text())
    sig = data.get("signature", data)
    # YAML tuples arrive as lists; coerce the date range.
    if isinstance(sig.get("date_code_range"), list):
        sig["date_code_range"] = tuple(sig["date_code_range"])
    return CircuitSignature(**sig)


def load_all_signatures(references_dir: Path | None = None) -> list[CircuitSignature]:
    references_dir = references_dir or config.REFERENCES_DIR
    sigs: list[CircuitSignature] = []
    for p in sorted(references_dir.glob("*.yaml")):
        if p.stem == "date_codes":
            continue
        try:
            sigs.append(load_signature(p))
        except Exception as e:  # surface bad fixtures loudly, don't swallow
            raise ValueError(f"invalid reference fixture {p.name}: {e}") from e
    return sigs
