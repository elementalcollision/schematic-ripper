"""Deterministic component-value parsing and normalization.

Turns the verbatim markings vision reads — ".1mfd 400vdc", "220k", a carbon-comp
resistor's colour bands — into canonical values: a human string (``value``) plus
an SI float (``value_si``: ohms for resistors/pots, farads for caps) so the
matcher can compare 100k == 0.1M == 100kΩ. Pure tables + regex, no API calls.

Vintage notation is first-class: in 1960s amp practice "MFD"/"mfd"/"mF" all mean
microfarads, and "MMFD"/"µµF" mean picofarads — not the SI millifarad/micro you
would assume today.
"""

from __future__ import annotations

import re

from .models import Component, ComponentType

# --- Resistor colour code -------------------------------------------------

_DIGIT = {
    "black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4,
    "green": 5, "blue": 6, "violet": 7, "purple": 7, "gray": 8, "white": 9,
}
_MULT = {
    "black": 1, "brown": 10, "red": 100, "orange": 1e3, "yellow": 1e4,
    "green": 1e5, "blue": 1e6, "violet": 1e7, "gray": 1e8, "white": 1e9,
    "gold": 0.1, "silver": 0.01,
}
_TOL = {
    "brown": "1%", "red": "2%", "green": "0.5%", "blue": "0.25%",
    "violet": "0.1%", "gray": "0.05%", "gold": "5%", "silver": "10%", "none": "20%",
}


def decode_resistor_bands(bands: list[str]) -> tuple[float, str] | None:
    """Decode 3/4/5/6-band resistor colours (left-to-right) -> (ohms, tolerance).

    Returns None on any unrecognized colour rather than guessing.
    """
    b = [x.strip().lower().replace("grey", "gray") for x in bands if x and x.strip()]
    if len(b) < 3:
        return None
    try:
        if len(b) >= 5:  # 5/6-band: 3 significant digits + multiplier (+ tol)
            sig = _DIGIT[b[0]] * 100 + _DIGIT[b[1]] * 10 + _DIGIT[b[2]]
            mult = _MULT[b[3]]
            tol = _TOL.get(b[4], "")
        else:            # 3/4-band: 2 significant digits + multiplier (+ tol)
            sig = _DIGIT[b[0]] * 10 + _DIGIT[b[1]]
            mult = _MULT[b[2]]
            tol = _TOL.get(b[3] if len(b) > 3 else "none", "20%")
    except KeyError:
        return None
    return sig * mult, tol


# --- Resistor text --------------------------------------------------------

_R_INFIX = re.compile(r"^(\d+)([kmr])(\d+)$", re.I)        # 4k7, 1k0, 2m2
_R_SUFFIX = re.compile(r"^(\d+(?:\.\d+)?)(k|meg|m|r)?$", re.I)
_R_MULT = {"k": 1e3, "m": 1e6, "meg": 1e6, "r": 1.0}


def parse_resistor(text: str | None) -> float | None:
    """Parse a printed resistance ('220k', '1M', '4k7', '470R', '2.2meg') -> ohms.

    In resistor context a bare 'm'/'M' means mega (not milli)."""
    if not text:
        return None
    t = re.sub(r"(ohms?|Ω)", "", text.strip(), flags=re.I).replace(" ", "")
    if not t:
        return None
    m = _R_INFIX.match(t)
    if m:
        whole, suf, frac = m.groups()
        return float(f"{whole}.{frac}") * _R_MULT[suf.lower()]
    m = _R_SUFFIX.match(t)
    if m:
        num, suf = m.groups()
        return float(num) * (_R_MULT[suf.lower()] if suf else 1.0)
    return None


# --- Capacitor text -------------------------------------------------------

# Ordered: picofarad spellings first so "mmfd" isn't caught by the "mfd" rule.
_CAP_UNITS = [
    (r"(?:µµf|uuf|mmfd|mmf|pfd|pf)", 1e-12),
    (r"(?:nfd|nf)", 1e-9),
    (r"(?:µfd|µf|ufd|uf|mfd|mf)", 1e-6),   # vintage MFD/mfd == microfarad
]
_VOLT = re.compile(r"(\d+)\s*v\.?\s*d?\.?\s*c?\.?", re.I)


def parse_capacitor(text: str | None) -> tuple[float | None, str | None]:
    """Parse a cap marking -> (farads, voltage). Handles vintage units and a
    voltage like '400vdc' / '400 V.D.C.'."""
    if not text:
        return None, None
    t = text.lower()
    farads = None
    for unit_pat, scale in _CAP_UNITS:
        m = re.search(r"(\d*\.?\d+)\s*" + unit_pat, t)
        if m:
            farads = float(m.group(1)) * scale
            break
    volts = None
    mv = _VOLT.search(text)
    if mv and ("v" in text.lower()):
        volts = f"{mv.group(1)}VDC"
    return farads, volts


def parse_ceramic_code(code: str | None) -> float | None:
    """Decode a 2/3-digit ceramic/film cap code -> farads ('103' -> 10nF)."""
    if not code or not re.fullmatch(r"\d{2,3}", code.strip()):
        return None
    c = code.strip()
    if len(c) == 2:
        return float(c) * 1e-12
    return int(c[:2]) * (10 ** int(c[2])) * 1e-12


# --- Formatting + comparison ---------------------------------------------

def format_ohms(o: float) -> str:
    if o >= 1e6:
        return f"{o / 1e6:g}MΩ"
    if o >= 1e3:
        return f"{o / 1e3:g}kΩ"
    return f"{o:g}Ω"


def format_farads(f: float) -> str:
    if f < 1e-9:
        return f"{f * 1e12:g}pF"
    if f < 1e-6:
        return f"{f * 1e9:g}nF"
    return f"{f * 1e6:g}µF"


def values_close(a: float | None, b: float | None, rel: float = 0.15) -> bool:
    """Tolerance-aware equality for SI values (default ±15%)."""
    if a is None or b is None:
        return False
    return abs(a - b) <= rel * max(abs(a), abs(b))


# --- Component normalization ---------------------------------------------

def normalize_component(comp: Component) -> Component:
    """Fill ``value`` / ``value_si`` / ``tolerance`` / ``voltage`` from a
    component's raw marking and colour bands. Returns a copy; non-passive parts
    (tubes, transformers) pass through unchanged."""
    updates: dict = {}

    if comp.type in (ComponentType.RESISTOR, ComponentType.POT):
        ohms = None
        if comp.color_bands:
            decoded = decode_resistor_bands(comp.color_bands)
            if decoded:
                ohms, tol = decoded
                updates["tolerance"] = comp.tolerance or tol
        if ohms is None:
            ohms = parse_resistor(comp.value) or parse_resistor(comp.raw_marking)
        if ohms is not None:
            updates["value_si"] = ohms
            updates["value"] = format_ohms(ohms)

    elif comp.type in (ComponentType.CAPACITOR, ComponentType.ELECTROLYTIC):
        farads, volts = parse_capacitor(comp.raw_marking or comp.value)
        if farads is None and comp.raw_marking:
            farads = parse_ceramic_code(comp.raw_marking)
        if farads is not None:
            updates["value_si"] = farads
            updates["value"] = format_farads(farads)
        if volts and not comp.voltage:
            updates["voltage"] = volts

    return comp.model_copy(update=updates) if updates else comp
