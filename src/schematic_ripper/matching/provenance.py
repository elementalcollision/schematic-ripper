"""Turn the scorecard into a provenance verdict.

Two independent axes:
  * WHICH revision  — top of the discriminator ranking.
  * GENUINE vs CLONE vs MODIFIED — a separate judgement from manufacturer +
    date-code coherence. A recap (modern filter caps over original molded caps)
    makes an amp MODIFIED, not fake; we surface that explicitly so it does not
    corrupt the genuineness call.
"""

from __future__ import annotations

from ..models import BOM, CircuitSignature, ProvenanceReport
from . import discriminators


def _is_modified(bom: BOM) -> bool:
    return any(
        (p.note or "").lower().startswith("modern")
        for c in bom.items
        for p in c.provenance
    )


def _genuine_vs_clone(bom: BOM, top: CircuitSignature, rows) -> str:
    # Transformer part-number agreement is the strongest genuineness signal.
    tx_rows = [r for r in rows if r.feature.startswith("transformer:")]
    tx_matches = sum(1 for r in tx_rows if r.verdict == "match")
    tx_mismatch = any(r.verdict == "mismatch" for r in tx_rows)

    if tx_mismatch:
        return "clone"
    if tx_matches >= 1:
        return "genuine"
    # No transformer evidence either way: fall back to construction coherence.
    vintage_makers = {"sprague", "good-all", "astron", "cornell"}
    seen = {(c.manufacturer or "").lower() for c in bom.items}
    if seen & vintage_makers:
        return "genuine"  # period-correct construction, pending transformer read
    return "indeterminate"


def assess(bom: BOM, signatures: list[CircuitSignature]) -> ProvenanceReport:
    ranked = discriminators.rank(bom, signatures)
    if not ranked:
        return ProvenanceReport(
            identified_model="unknown",
            confidence=0.0,
            genuine_vs_clone="indeterminate",
            bom=bom,
            summary="No reference signatures available to match against.",
        )

    top_sig, top_score, top_rows = ranked[0]
    runner = ranked[1][0].model if len(ranked) > 1 else None

    # Confidence: positive normalized score, widened by margin over runner-up.
    margin = top_score - (ranked[1][1] if len(ranked) > 1 else 0.0)
    confidence = max(0.0, min(1.0, 0.5 * max(0.0, top_score) + 0.5 * min(1.0, margin + max(0.0, top_score))))

    modified = _is_modified(bom)
    genuineness = _genuine_vs_clone(bom, top_sig, top_rows)
    if genuineness == "genuine" and modified:
        genuineness = "genuine (modified)"

    return ProvenanceReport(
        identified_model=top_sig.model,
        confidence=round(confidence, 3),
        genuine_vs_clone=genuineness,
        is_modified=modified,
        feature_matches=top_rows,
        runner_up=runner,
        bom=bom,
        summary=(
            f"Best match: {top_sig.family} {top_sig.model} "
            f"(normalized score {top_score:+.2f}"
            + (f", runner-up {runner}" if runner else "")
            + ")."
        ),
    )
