"""Deterministic value parsing: colour bands, resistor/cap text, normalization."""

import pytest

from schematic_ripper import values
from schematic_ripper.models import Component, ComponentType, ExtractionMethod, Provenance


@pytest.mark.parametrize(
    "bands, ohms, tol",
    [
        (["brown", "black", "red", "gold"], 1000, "5%"),
        (["yellow", "violet", "orange", "gold"], 47000, "5%"),
        (["brown", "black", "black", "brown", "brown"], 1000, "1%"),  # 5-band
        (["green", "blue", "yellow", "silver"], 560000, "10%"),
    ],
)
def test_resistor_band_decode(bands, ohms, tol):
    assert values.decode_resistor_bands(bands) == (pytest.approx(ohms), tol)


def test_resistor_band_decode_rejects_garbage():
    assert values.decode_resistor_bands(["mauve", "black", "red"]) is None


@pytest.mark.parametrize(
    "text, ohms",
    [("220k", 220_000), ("1M", 1_000_000), ("4k7", 4700), ("470R", 470),
     ("2.2meg", 2_200_000), ("100", 100), ("1k0", 1000)],
)
def test_resistor_text(text, ohms):
    assert values.parse_resistor(text) == pytest.approx(ohms)


@pytest.mark.parametrize(
    "text, farads, volts",
    [
        (".1mfd 400vdc", 1e-7, "400VDC"),
        ("MOLDED .047 mfd 400 vdc", 4.7e-8, "400VDC"),
        ("20uF 500VDC", 2e-5, "500VDC"),
        ("80 MFD", 8e-5, None),
        ("470pf", 4.7e-10, None),
        ("100mmfd", 1e-10, None),
    ],
)
def test_capacitor_text(text, farads, volts):
    f, v = values.parse_capacitor(text)
    assert f == pytest.approx(farads)
    assert v == volts


def test_ceramic_code():
    assert values.parse_ceramic_code("103") == pytest.approx(1e-8)
    assert values.parse_ceramic_code("473") == pytest.approx(4.7e-8)
    assert values.parse_ceramic_code("400") == pytest.approx(4e-11)  # 40 x 10^0 pF = 40pF


def test_formatting_and_closeness():
    assert values.format_ohms(4700) == "4.7kΩ"
    assert values.format_farads(1e-7) == "100nF"
    assert values.values_close(100_000, 0.1e6)        # 100k == 0.1M
    assert not values.values_close(100_000, 250_000)


def test_normalize_component_cap():
    c = Component(
        type=ComponentType.CAPACITOR,
        raw_marking="MOLDED .1mfd 400vdc Made in U.S.",
        provenance=[Provenance(method=ExtractionMethod.CLAUDE_VISION)],
    )
    n = values.normalize_component(c)
    assert n.value_si == pytest.approx(1e-7)
    assert n.value == "100nF"
    assert n.voltage == "400VDC"


def test_normalize_component_resistor_from_bands():
    c = Component(
        type=ComponentType.RESISTOR,
        color_bands=["yellow", "violet", "orange", "gold"],
        provenance=[Provenance(method=ExtractionMethod.CLAUDE_VISION)],
    )
    n = values.normalize_component(c)
    assert n.value_si == pytest.approx(47000)
    assert n.tolerance == "5%"
    assert n.value == "47kΩ"
