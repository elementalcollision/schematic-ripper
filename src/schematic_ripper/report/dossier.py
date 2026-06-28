"""Render a ProvenanceReport as a Markdown dossier.

Every discriminator row cites its evidence, so a reader can audit *why* the verdict
landed where it did — that traceability is the deliverable, not just the verdict.
"""

from __future__ import annotations

from ..models import ProvenanceReport

_VERDICT_ICON = {"match": "✓", "mismatch": "✗", "unknown": "·"}


def to_markdown(report: ProvenanceReport) -> str:
    lines: list[str] = []
    lines.append("# Provenance Dossier\n")
    lines.append(f"**Identified model:** {report.identified_model}  ")
    lines.append(f"**Confidence:** {report.confidence:.0%}  ")
    lines.append(f"**Authenticity:** {report.genuine_vs_clone}  ")
    lines.append(f"**Modified from original:** {'yes' if report.is_modified else 'no'}  ")
    if report.runner_up:
        lines.append(f"**Runner-up:** {report.runner_up}  ")
    lines.append("")
    if report.summary:
        lines.append(f"> {report.summary}\n")

    lines.append("## Discriminator scorecard\n")
    lines.append("| | Feature | Expected | Observed | Weight |")
    lines.append("|---|---|---|---|---|")
    for r in report.feature_matches:
        icon = _VERDICT_ICON.get(r.verdict, "?")
        lines.append(
            f"| {icon} | {r.feature} | {r.expected or '—'} | {r.observed or '—'} | {r.weight:g} |"
        )
    lines.append("")

    if report.bom and report.bom.items:
        lines.append("## Extracted bill of materials\n")
        lines.append("| Type | Value | Marking | Mfr | Date code | Source |")
        lines.append("|---|---|---|---|---|---|")
        for c in report.bom.items:
            src = ", ".join(sorted({p.source_image or p.source_doc or "" for p in c.provenance}))
            value = c.value or c.part_number or "—"  # tubes/transformers carry id in part_number
            lines.append(
                f"| {c.type.value} | {value} | {c.raw_marking or '—'} | "
                f"{c.manufacturer or '—'} | {c.date_code or '—'} | {src} |"
            )
        lines.append("")

    return "\n".join(lines)
