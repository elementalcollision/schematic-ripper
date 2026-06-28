"""Turn the scorecard into a provenance verdict.

Two independent axes:
  * WHICH revision  — top of the discriminator ranking.
  * GENUINE vs CLONE vs MODIFIED — a separate judgement from manufacturer +
    date-code coherence. A recap (modern filter caps over original molded caps)
    makes an amp MODIFIED, not fake; we surface that explicitly so it does not
    corrupt the genuineness call.
"""

from __future__ import annotations

from ..models import BOM, CircuitSignature, ComponentType, ProvenanceReport
from . import discriminators

# Notes that mark a part as a service replacement / non-original.
_REPLACEMENT_PREFIXES = ("modern", "replacement", "non-oe", "non-original", "reissue")


def _is_replacement(comp) -> bool:
    return any(
        (p.note or "").lower().startswith(_REPLACEMENT_PREFIXES) for p in comp.provenance
    )


def _is_modified(bom: BOM) -> bool:
    return any(_is_replacement(c) for c in bom.items)


def _genuine_vs_clone(bom: BOM, top: CircuitSignature, rows) -> str:
    """Authenticity rests on ORIGINAL construction, not on swappable iron.

    Transformers and filter caps are routinely replaced, so a non-OE transformer
    says nothing about whether the amp is a genuine example — that is service
    history, captured separately as ``is_modified``. We judge genuine/clone from
    period-correct construction among the *non-replaced* parts, plus an original
    (non-replaced) transformer stamp if one happens to match. 'clone' is asserted
    only on a positive signal; absent one we say 'indeterminate' rather than guess.
    """
    matched_pns = {
        r.expected.upper()
        for r in rows
        if r.feature.startswith("transformer:") and r.verdict == "match" and r.expected
    }
    original_tx_match = any(
        not _is_replacement(c) and (c.part_number or "").upper() in matched_pns
        for c in bom.items
        if c.type in (ComponentType.TRANSFORMER, ComponentType.CHOKE)
    )

    vintage_makers = {"sprague", "good-all", "astron", "cornell", "cornell-dubilier"}
    original_makers = {
        (c.manufacturer or "").lower() for c in bom.items if not _is_replacement(c)
    }
    construction_genuine = bool(original_makers & vintage_makers)

    if original_tx_match or construction_genuine:
        return "genuine"
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
