"""v2 — topology confirmation via VF2 subgraph isomorphism.

NOT on the v1 critical path. Once a human has traced nets into a Netlist, this
confirms the scorecard's top candidate by checking structural agreement. We use
VF2 (`GraphMatcher`) with node/edge predicates — never optimal graph-edit-distance,
which is NP-hard and routinely fails to terminate on real circuits.
"""

from __future__ import annotations

from ..models import Netlist


def confirm_topology(extracted: Netlist, reference: Netlist) -> dict:
    """Return a structural-agreement summary. Requires `networkx` (extra: graph)."""
    import networkx as nx
    from networkx.algorithms import isomorphism

    g_ext = extracted.to_networkx()
    g_ref = reference.to_networkx()

    def node_match(a, b):
        return a.get("type") == b.get("type")

    gm = isomorphism.GraphMatcher(g_ref, g_ext, node_match=node_match)
    return {
        "subgraph_isomorphic": gm.subgraph_is_isomorphic(),
        "ref_nodes": g_ref.number_of_nodes(),
        "ext_nodes": g_ext.number_of_nodes(),
        "ref_edges": g_ref.number_of_edges(),
        "ext_edges": g_ext.number_of_edges(),
    }
