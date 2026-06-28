"""v2 — stylized eyelet-board layout diagram.

Mirrors the Fender "layout" document style (the 6G6-B reference is one): tube
sockets along the top, the eyelet board with components placed left-to-right.
Built on schemdraw's element/anchor grid; no KiCad PCB stack required.

Stub until the v2 netlist exists — placement needs net membership.
"""

from __future__ import annotations

from pathlib import Path

from ..models import Netlist


def render_eyelet_layout(netlist: Netlist, out_path: Path) -> Path:
    raise NotImplementedError(
        "Eyelet-board layout rendering is a v2 feature; it requires a confirmed "
        "Netlist with net membership (see matching/graph_match.py)."
    )
