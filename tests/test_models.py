"""The data spine round-trips and the BOM helpers read the right facts."""

from schematic_ripper.models import (
    BOM,
    Component,
    ComponentType,
    ExtractionMethod,
    Provenance,
)


def _comp(type_, **kw):
    return Component(type=type_, provenance=[Provenance(method=ExtractionMethod.HUMAN)], **kw)


def test_bom_tube_and_transformer_helpers():
    bom = BOM(
        source="t",
        items=[
            _comp(ComponentType.TUBE, part_number="5881"),
            _comp(ComponentType.TUBE, part_number="7025"),
            _comp(ComponentType.TRANSFORMER, part_number="125P7A"),
            _comp(ComponentType.DIODE),
        ],
    )
    assert set(bom.tubes) == {"5881", "7025"}
    assert bom.transformer_part_numbers == ["125P7A"]
    assert bom.has_diode_rectifier() is True
    assert bom.has_rectifier_tube() is False


def test_rectifier_tube_detection():
    bom = BOM(source="t", items=[_comp(ComponentType.TUBE, part_number="GZ34")])
    assert bom.has_rectifier_tube() is True


def test_component_json_roundtrip():
    c = _comp(ComponentType.CAPACITOR, value="0.1uF", raw_marking=".1mfd 400vdc")
    assert Component.model_validate_json(c.model_dump_json()).raw_marking == ".1mfd 400vdc"
