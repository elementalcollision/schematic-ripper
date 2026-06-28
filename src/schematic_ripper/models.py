"""The shared data spine.

One representation serves both reference circuits (hand-authored, fully
connected) and extracted circuits (BOM-only in v1). Every fact carries a
:class:`Provenance` so the final dossier is auditable down to the source image
and region — that auditability is the project's actual product.

This module depends on nothing else in the package. Import it everywhere.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    RESISTOR = "R"
    CAPACITOR = "C"          # film / paper / ceramic
    ELECTROLYTIC = "CE"      # polarized electrolytic
    TUBE = "V"               # vacuum tube / valve
    TRANSFORMER = "T"        # power / output transformer
    CHOKE = "L"              # filter choke / inductor
    DIODE = "D"              # incl. solid-state rectifier
    POT = "RV"               # potentiometer
    JACK = "J"
    SWITCH = "SW"
    SPEAKER = "LS"
    LAMP = "PL"              # pilot lamp
    OTHER = "X"


class ExtractionMethod(str, Enum):
    CLAUDE_VISION = "claude_vision"
    TESSERACT = "tesseract"
    OPENCV = "opencv"
    HUMAN = "human"
    REFERENCE_FIXTURE = "reference_fixture"


class Provenance(BaseModel):
    """Where a single fact came from. Attached to every extracted value."""

    method: ExtractionMethod
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_image: str | None = None          # e.g. "IMG_0987.jpeg"
    bbox: tuple[int, int, int, int] | None = None  # (x, y, w, h) in source image
    source_doc: str | None = None            # e.g. "Fender_bassman_6g6c.pdf"
    note: str | None = None


class Component(BaseModel):
    """A single physical part. `value` is normalized; `raw_marking` is verbatim.

    Vintage cap nomenclature (".1mfd 400vdc") must survive untouched *and* be
    normalized — never lose the original string, it is itself dating evidence.
    """

    type: ComponentType
    ref: str | None = None            # designator if known: "R12", "C7", "V1"
    value: str | None = None          # normalized human form: "4.7kΩ", "0.1µF"
    value_si: float | None = None     # canonical SI: ohms (R/RV), farads (C/CE)
    tolerance: str | None = None      # "5%", "10%"
    raw_marking: str | None = None    # verbatim: ".1mfd 400vdc Made in U.S."
    voltage: str | None = None        # "400VDC", "500VDC"
    color_bands: list[str] = Field(default_factory=list)  # resistor bands, read order
    part_number: str | None = None    # "125P7A", "5881", "7025"
    manufacturer: str | None = None   # "Sprague", "Good-All", "Nichicon"
    date_code: str | None = None      # raw stamp, e.g. "606", "137-XXX"
    pins: list[str] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)


class Net(BaseModel):
    """An electrical node. Empty in v1 (BOM-only); populated for references."""

    name: str                          # "B+", "node_7", "GND", "heater_6.3V"
    connections: list[tuple[str, str]] = Field(default_factory=list)  # (ref, pin)
    provenance: list[Provenance] = Field(default_factory=list)


class Netlist(BaseModel):
    name: str
    components: list[Component] = Field(default_factory=list)
    nets: list[Net] = Field(default_factory=list)

    def to_networkx(self):
        """Build a graph for v2 topology confirmation. Lazy import."""
        import networkx as nx

        g = nx.Graph()
        for c in self.components:
            g.add_node(c.ref or id(c), type=c.type.value, value=c.value)
        for net in self.nets:
            refs = [ref for ref, _pin in net.connections]
            for i in range(len(refs)):
                for j in range(i + 1, len(refs)):
                    g.add_edge(refs[i], refs[j], net=net.name)
        return g


class BOM(BaseModel):
    """Bill of materials — the v1 extracted representation (no nets required)."""

    source: str                        # "source_images/" or a doc name
    items: list[Component] = Field(default_factory=list)

    @property
    def tubes(self) -> list[str]:
        return [
            c.part_number
            for c in self.items
            if c.type is ComponentType.TUBE and c.part_number
        ]

    @property
    def transformer_part_numbers(self) -> list[str]:
        return [
            c.part_number
            for c in self.items
            if c.type in (ComponentType.TRANSFORMER, ComponentType.CHOKE) and c.part_number
        ]

    def has_diode_rectifier(self) -> bool:
        return any(c.type is ComponentType.DIODE for c in self.items)

    def has_rectifier_tube(self) -> bool:
        rect = {"5U4", "5U4GA", "5U4GB", "GZ34", "5AR4", "5Y3"}
        return any(
            c.type is ComponentType.TUBE and (c.part_number or "").upper() in rect
            for c in self.items
        )


class CircuitSignature(BaseModel):
    """The per-revision discriminator spec the scorecard matches against.

    Data-driven on purpose: adding AA864 / AB165 later is a YAML edit, not code.
    """

    model: str                         # "6G6-C"
    family: str = "Fender Bassman"
    rectifier_type: str                # "solid_state" | "tube_GZ34" | "tube_5U4GB"
    required_tubes: list[str] = Field(default_factory=list)
    transformer_part_numbers: list[str] = Field(default_factory=list)
    diagnostic_values: dict[str, str] = Field(default_factory=dict)  # role -> value
    date_code_range: tuple[int, int] | None = None  # (year_from, year_to)
    notes: str | None = None


class FeatureMatch(BaseModel):
    """One row of the scorecard. `verdict` drives a signed, weighted score."""

    feature: str
    expected: str | None = None
    observed: str | None = None
    verdict: str                       # "match" | "mismatch" | "unknown"
    weight: float = 1.0
    evidence: list[Provenance] = Field(default_factory=list)

    @property
    def score(self) -> float:
        return {"match": 1.0, "unknown": 0.0, "mismatch": -1.0}[self.verdict] * self.weight


class ProvenanceReport(BaseModel):
    identified_model: str
    confidence: float = Field(ge=0.0, le=1.0)
    genuine_vs_clone: str              # "genuine" | "clone" | "modified" | "indeterminate"
    is_modified: bool = False
    feature_matches: list[FeatureMatch] = Field(default_factory=list)
    runner_up: str | None = None
    bom: BOM | None = None
    summary: str | None = None
