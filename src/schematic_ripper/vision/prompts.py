"""Prompt + tool schema for structured component extraction.

We force a tool call so the model returns validated JSON, not prose. The schema
mirrors :class:`schematic_ripper.models.Component`. Crucially we ask for the
verbatim marking AND a normalized value, and we forbid guessing connectivity —
v1 extracts identity, never nets.
"""

from __future__ import annotations

SYSTEM = """You are a meticulous vintage-electronics technician examining a
close-up photograph of a tube-amplifier chassis (point-to-point / eyelet board).
Identify every electronic component you can see clearly. For each one report its
type, the VERBATIM text printed on it, a normalized value, voltage rating,
manufacturer, and any date code.

Rules:
- Only report what is legible. If a value is unreadable, omit it — never guess.
- Preserve original markings exactly, including vintage notation like ".1mfd",
  "MFD", "V.D.C.", "OUTSIDE FOIL".
- For carbon-composition resistors, report the colour bands left-to-right in
  `color_bands` (do not decode them — the parser does that deterministically).
- Identify tube types from glass/socket silkscreen (e.g. 5881, 7025, GZ34).
- Read transformer/choke part-number and date-code stamps when present —
  these are the strongest provenance evidence.
- Do NOT infer wiring, nets, or connectivity. Identity only.
- Flag obviously modern replacement parts (e.g. Nichicon, modern Vishay) since
  they indicate later service work."""

# Tool schema handed to the Anthropic SDK (tool_choice forces it).
EXTRACT_TOOL = {
    "name": "report_components",
    "description": "Report the components legible in this chassis photo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "components": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "R", "C", "CE", "V", "T", "L", "D",
                                "RV", "J", "SW", "LS", "PL", "X",
                            ],
                            "description": "Component type code.",
                        },
                        "value": {"type": "string", "description": "Printed value if legible, e.g. '220k', '0.1uF'."},
                        "color_bands": {"type": "array", "items": {"type": "string"}, "description": "Resistor colour bands left-to-right, e.g. ['brown','black','red','gold']. Report colours; do not decode."},
                        "tolerance": {"type": "string", "description": "e.g. '5%', '10%'."},
                        "raw_marking": {"type": "string", "description": "Verbatim printed text."},
                        "voltage": {"type": "string"},
                        "part_number": {"type": "string"},
                        "manufacturer": {"type": "string"},
                        "date_code": {"type": "string"},
                        "is_modern_replacement": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["type", "confidence"],
                },
            }
        },
        "required": ["components"],
    },
}
