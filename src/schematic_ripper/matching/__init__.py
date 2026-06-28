"""Matching layer. The scorecard (discriminators.py) is the v1 critical path;
graph isomorphism (graph_match.py) is an optional v2 confirmation only.

This package consumes confirmed BOM objects and never imports the vision layer,
so it is fully unit-testable without API calls."""
