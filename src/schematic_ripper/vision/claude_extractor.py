"""Claude multimodal component extraction — the v1 workhorse.

Sends each chassis photo to Claude with a forced tool call and maps the result
into :class:`Component` objects tagged with :class:`Provenance`. Network/topology
is deliberately out of scope here; this stage answers "what parts are present",
which is exactly what the provenance scorecard needs.
"""

from __future__ import annotations

import base64
from pathlib import Path

from .. import values
from ..models import Component, ComponentType, ExtractionMethod, Provenance
from . import prompts


def _media_type(path: Path) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(path.suffix.lower(), "image/jpeg")


def extract_components(image_path: Path, model: str | None = None) -> list[Component]:
    """Extract legible components from a single chassis photo via Claude vision."""
    import anthropic

    from .. import config

    model = model or config.VISION_MODEL
    data = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=prompts.SYSTEM,
        tools=[prompts.EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "report_components"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _media_type(image_path),
                            "data": data,
                        },
                    },
                    {"type": "text", "text": "Report every component you can read clearly."},
                ],
            }
        ],
    )

    block = next((b for b in resp.content if b.type == "tool_use"), None)
    if block is None:
        return []
    return _to_components(block.input.get("components", []), image_path.name)


def _to_components(raw: list[dict], source_image: str) -> list[Component]:
    out: list[Component] = []
    for r in raw:
        note = "modern replacement" if r.get("is_modern_replacement") else None
        comp = Component(
            type=ComponentType(r["type"]),
            value=r.get("value"),
            raw_marking=r.get("raw_marking"),
            voltage=r.get("voltage"),
            part_number=r.get("part_number"),
            manufacturer=r.get("manufacturer"),
            date_code=r.get("date_code"),
            color_bands=r.get("color_bands", []),
            tolerance=r.get("tolerance"),
            provenance=[
                Provenance(
                    method=ExtractionMethod.CLAUDE_VISION,
                    confidence=float(r.get("confidence", 0.5)),
                    source_image=source_image,
                    note=note,
                )
            ],
        )
        # Deterministic value parsing/normalization over the model's raw reads.
        out.append(values.normalize_component(comp))
    return out
