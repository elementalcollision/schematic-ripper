"""Weighted discriminator scorecard — the v1 matcher.

The reference library is tiny and known, and the features that separate revisions
are LOCAL and enumerable: rectifier type, tube complement, transformer part
numbers, a handful of diagnostic RC values. So we score each candidate
:class:`CircuitSignature` against the extracted :class:`BOM` with a weighted,
signed scorecard — no NP-hard graph-edit-distance on the critical path.

Each feature votes match (+w), unknown (0), or mismatch (-w). Hard discriminators
(rectifier, transformers) carry far more weight than a single resistor value.
"""

from __future__ import annotations

import re

from ..models import BOM, CircuitSignature, FeatureMatch

# Weights — hard discriminators dominate.
W_RECTIFIER = 5.0
W_TRANSFORMER = 4.0
W_TUBE = 3.0
W_VALUE = 1.0


def _value_present(bom: BOM, value: str) -> bool:
    """Whole-token value search. Boundary-aware so a pot value like "1M" does not
    spuriously match inside a cap marking such as ".1mfd"."""
    target = value.strip().lower()
    pat = re.compile(r"(?<![a-z0-9.])" + re.escape(target) + r"(?![a-z0-9])")
    for c in bom.items:
        for field in (c.value, c.raw_marking):
            if field and pat.search(field.lower()):
                return True
    return False


def score_signature(bom: BOM, sig: CircuitSignature) -> list[FeatureMatch]:
    """Build the scorecard rows for one candidate revision."""
    rows: list[FeatureMatch] = []

    # --- Rectifier type (hard) ---
    if sig.rectifier_type == "solid_state":
        observed = "solid_state" if bom.has_diode_rectifier() else (
            "tube" if bom.has_rectifier_tube() else "unknown"
        )
    else:
        observed = "tube" if bom.has_rectifier_tube() else (
            "solid_state" if bom.has_diode_rectifier() else "unknown"
        )
    expected = "solid_state" if sig.rectifier_type == "solid_state" else "tube"
    rows.append(
        FeatureMatch(
            feature="rectifier_type",
            expected=expected,
            observed=observed,
            verdict="match" if observed == expected else ("unknown" if observed == "unknown" else "mismatch"),
            weight=W_RECTIFIER,
        )
    )

    # --- Tube complement (hard) ---
    observed_tubes = {t.upper() for t in bom.tubes}
    for tube in sig.required_tubes:
        present = tube.upper() in observed_tubes
        rows.append(
            FeatureMatch(
                feature=f"tube:{tube}",
                expected=tube,
                observed=tube if present else None,
                verdict="match" if present else "unknown",  # absence may be unread, not wrong
                weight=W_TUBE,
            )
        )

    # --- Transformer part numbers (hard) ---
    observed_pns = {p.upper() for p in bom.transformer_part_numbers}
    for pn in sig.transformer_part_numbers:
        present = pn.upper() in observed_pns
        rows.append(
            FeatureMatch(
                feature=f"transformer:{pn}",
                expected=pn,
                observed=pn if present else None,
                verdict="match" if present else "unknown",
                weight=W_TRANSFORMER,
            )
        )

    # --- Diagnostic component values (soft) ---
    for role, value in sig.diagnostic_values.items():
        present = _value_present(bom, value)
        rows.append(
            FeatureMatch(
                feature=f"value:{role}",
                expected=value,
                observed=value if present else None,
                verdict="match" if present else "unknown",
                weight=W_VALUE,
            )
        )

    return rows


def rank(
    bom: BOM, signatures: list[CircuitSignature]
) -> list[tuple[CircuitSignature, float, list[FeatureMatch]]]:
    """Rank candidates by normalized scorecard. Returns sorted best-first.

    Normalized score = sum(signed weights) / sum(all weights), in [-1, 1].
    """
    results: list[tuple[CircuitSignature, float, list[FeatureMatch]]] = []
    for sig in signatures:
        rows = score_signature(bom, sig)
        total_weight = sum(r.weight for r in rows) or 1.0
        norm = sum(r.score for r in rows) / total_weight
        results.append((sig, norm, rows))
    results.sort(key=lambda r: r[1], reverse=True)
    return results
