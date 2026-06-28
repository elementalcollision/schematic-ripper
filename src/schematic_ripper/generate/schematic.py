"""Render the identified circuit as a clean schematic with schemdraw (pure
Python, SVG/PNG, no system deps).

v1 draws (a) a labeled signal-chain block diagram annotated with the identified
revision's tube complement, rectifier type, and transformer part numbers, and
(b) a detailed first triode gain stage. That is enough to *show* the matched
circuit; full per-net rendering arrives with the v2 netlist.
"""

from __future__ import annotations

from pathlib import Path

from ..models import CircuitSignature


def render_block_diagram(sig: CircuitSignature, out_path: Path) -> Path:
    """Draw the amp's signal chain as an annotated block diagram. Requires the
    `eda` extra (schemdraw)."""
    import schemdraw
    from schemdraw import flow

    rect = "SS rectifier" if sig.rectifier_type == "solid_state" else sig.rectifier_type
    tubes = " + ".join(sig.required_tubes) or "—"

    with schemdraw.Drawing(file=str(out_path)) as d:
        d.config(fontsize=11)
        d += flow.Box(w=2.2, h=1).label("INPUT\njack")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=2.4, h=1).label("Preamp\n12AX7/7025")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=2.4, h=1).label("Tone stack\nB / T / Presence")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=2.4, h=1).label("Phase\ninverter")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=2.6, h=1).label("Power\n2× 5881 PP")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=2.2, h=1).label("Output\ntransformer")
        d += flow.Arrow().right(d.unit / 2)
        d += flow.Box(w=1.8, h=1).label("SPKR")
        d += flow.Box(w=13, h=0.9).at((0, -2.2)).label(
            f"{sig.family} {sig.model}   |   tubes: {tubes}   |   {rect}   "
            f"|   transformers: {', '.join(sig.transformer_part_numbers) or '—'}"
        )
    return out_path


def render_gain_stage(out_path: Path) -> Path:
    """Draw a detailed 12AX7 common-cathode gain stage (the recurring building
    block of the Bassman preamp). Requires the `eda` extra (schemdraw)."""
    import schemdraw
    import schemdraw.elements as elm

    with schemdraw.Drawing(file=str(out_path)) as d:
        d.config(fontsize=11)
        d += (vin := elm.Dot(open=True).label("IN", "left"))
        d += elm.Resistor().right().label("68k\ngrid stop")
        d += (grid := elm.Dot())
        d += elm.Resistor().down().label("1M\ngrid ref").at(grid.start)
        d += elm.Ground()
        d += elm.Line().up().at(grid.start).length(d.unit / 2)
        d += elm.Triode().right().label("V1\n½ 12AX7")
        d += elm.Line().up().length(d.unit / 2)
        d += elm.Resistor().up().label("100k\nplate")
        d += elm.Vdd().label("+300V")
        d += elm.Line().right().length(d.unit / 2)
        d += elm.Dot().label("OUT", "right")
    return out_path
