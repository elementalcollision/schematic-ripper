"""Date-code decoding for Fender-era provenance.

Two facts do most of the dating work on a 1960s Fender:
  * EIA source-date codes on transformers and pots — "606-XXX" => EIA source 606
    (Schumacher) made in week/year, "137" => CTS. The trailing digits give
    year+week (e.g. "...6312" => 1963 week 12).
  * Tube and cap manufacturer + date stamps.

This module decodes what it can and leaves the rest to the human-confirmation
step. It is intentionally small and data-driven; extend the tables, not the code.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .. import config

# EIA manufacturer source codes most relevant to vintage Fender amps.
EIA_SOURCE_CODES = {
    "606": "Schumacher",   # Fender's main transformer vendor
    "137": "CTS",          # pots / speakers
    "304": "Stackpole",    # pots / resistors
    "274": "Jensen",       # speakers
}


def load_date_code_table(references_dir: Path | None = None) -> dict:
    references_dir = references_dir or config.REFERENCES_DIR
    p = references_dir / "date_codes.yaml"
    if p.exists():
        return yaml.safe_load(p.read_text()) or {}
    return {}


def decode_eia(stamp: str) -> dict | None:
    """Decode an EIA source-date code like '606-341' or '1376312'.

    Returns {source, year, week} where derivable. Best-effort: real stamps are
    inconsistent, so unknowns are left out rather than guessed.
    """
    digits = "".join(ch for ch in stamp if ch.isdigit())
    if len(digits) < 3:
        return None
    source = EIA_SOURCE_CODES.get(digits[:3])
    out: dict = {"source_code": digits[:3], "source": source}
    tail = digits[3:]
    if len(tail) >= 3:  # YWW or YYWW
        if len(tail) == 3:
            out["year"] = 1960 + int(tail[0])  # single-digit year, 1960s context
            out["week"] = int(tail[1:3])
        elif len(tail) >= 4:
            out["year"] = 1900 + int(tail[:2])
            out["week"] = int(tail[2:4])
    return out
