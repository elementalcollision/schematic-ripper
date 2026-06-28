"""The scorecard ranks the right family and stays honest about B vs C."""

from schematic_ripper.matching import discriminators, provenance
from schematic_ripper.models import (
    BOM,
    Component,
    ComponentType,
    CircuitSignature,
    ExtractionMethod,
    Provenance,
)


def _human(note=None):
    return [Provenance(method=ExtractionMethod.HUMAN, note=note)]


def _bassman_signatures():
    common = dict(
        family="Fender Bassman",
        rectifier_type="solid_state",
        required_tubes=["5881", "7025"],
    )
    return [
        CircuitSignature(model="6G6-B", transformer_part_numbers=["125P7A"], **common),
        CircuitSignature(
            model="6G6-C",
            transformer_part_numbers=["125P7A", "125C1A", "125A13A"],
            diagnostic_values={"plate_supply": "430V"},
            **common,
        ),
    ]


def test_transformer_stamp_resolves_6g6c():
    bom = BOM(
        source="t",
        items=[
            Component(type=ComponentType.TUBE, part_number="5881", provenance=_human()),
            Component(type=ComponentType.TUBE, part_number="7025", provenance=_human()),
            Component(type=ComponentType.DIODE, provenance=_human()),
            Component(type=ComponentType.TRANSFORMER, part_number="125A13A", provenance=_human()),
            Component(type=ComponentType.CHOKE, part_number="125C1A", provenance=_human()),
        ],
    )
    ranked = discriminators.rank(bom, _bassman_signatures())
    assert ranked[0][0].model == "6G6-C"  # unique transformer stamps win


def test_value_match_is_boundary_aware():
    # "1M" (a pot value) must NOT match inside ".1mfd" (a cap marking).
    caps = BOM(
        source="t",
        items=[Component(type=ComponentType.CAPACITOR, raw_marking="MOLDED .1mfd 400vdc",
                         provenance=_human())],
    )
    assert discriminators._value_present(caps, "1M") is False
    pot = BOM(
        source="t",
        items=[Component(type=ComponentType.POT, value="1M-A", provenance=_human())],
    )
    assert discriminators._value_present(pot, "1M") is True


def test_non_oe_transformer_excluded_from_authenticity():
    # A replaced (non-OE) transformer is service history, not a clone signal — and
    # its stamp must not be used as genuineness evidence even if the PN matches.
    bom = BOM(
        source="t",
        items=[
            Component(type=ComponentType.TUBE, part_number="5881", provenance=_human()),
            Component(
                type=ComponentType.TRANSFORMER, part_number="125A13A",
                provenance=[Provenance(method=ExtractionMethod.HUMAN,
                                       note="non-OE replacement output transformer")],
            ),
        ],
    )
    report = provenance.assess(bom, _bassman_signatures())
    assert report.is_modified is True
    assert report.genuine_vs_clone != "clone"


def test_recap_flagged_modified_not_clone():
    bom = BOM(
        source="t",
        items=[
            Component(type=ComponentType.TUBE, part_number="5881", provenance=_human()),
            Component(type=ComponentType.ELECTROLYTIC, manufacturer="Sprague",
                      provenance=_human("modern replacement filter cap")),
        ],
    )
    report = provenance.assess(bom, _bassman_signatures())
    assert report.is_modified is True
    assert "modified" in report.genuine_vs_clone or report.genuine_vs_clone == "indeterminate"
