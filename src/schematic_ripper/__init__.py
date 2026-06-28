"""Schematic Ripper — photo-to-provenance for vacuum-tube amplifiers.

Pipeline: ingest -> vision extraction -> human confirmation -> discriminator
matching -> provenance report -> schematic generation.

The data spine lives in :mod:`schematic_ripper.models`; every other module
imports it and nothing else from the package, so the matcher and report layers
are testable without API calls.
"""

__version__ = "0.1.0"

from .models import (  # noqa: F401
    BOM,
    Component,
    ComponentType,
    CircuitSignature,
    FeatureMatch,
    Net,
    Netlist,
    Provenance,
    ProvenanceReport,
)
