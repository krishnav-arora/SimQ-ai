"""
Milestone 2 path-level simulation utilities.
"""

from __future__ import annotations
import networkx as nx
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from . import config
from .link_models import (
    simulate_quantum_hop,
    simulate_entanglement_swap,
    simulate_classical_hop,
)


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------
def _nodes_support_quantum(G: nx.Graph, u: int, v: int) -> bool:
    return G.nodes[u].get("quantum", False) and G.nodes[v].get("quantum", False)


def _node_can_swap(G: nx.Graph, n: int) -> bool:
    return G.nodes[n].get("can_store_entanglement", False)


# -----------------------------------------------------------
# Quantum path simulation
# -----------------------------------------------------------
def simulate_path_quantum(G: nx.Graph, path: List[int]):
    """
    Attempt to distribute end-to-end entanglement across path.
    Model: each edge must support quantum; each *intermediate* node must be able to swap.
    If any fails, whole path fails.
    """
    metrics = {
        "hops": len(path) - 1,
        "mode": "quantum_path",
        "total_distance_km": 0.0,
        "success": False,
    }

    # Edge-wise attempts
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.edges[u, v]
        success, m = simulate_quantum_hop(edge_data)
        metrics["total_distance_km"] += m["distance_km"]
        if not success:
            return metrics  # fail early

        # After a successful hop, if not last edge, need swap at the intermediate node v
        if i < len(path) - 2:
            swap_ok, p = simulate_entanglement_swap(_node_can_swap(G, v))
            if not swap_ok:
                return metrics  # fail at swap

    # If we got here, all hops & swaps passed
    metrics["success"] = True
    return metrics


# -----------------------------------------------------------
# Classical path simulation
# -----------------------------------------------------------
def simulate_path_classical(G: nx.Graph, path: List[int]):
    metrics = {
        "hops": len(path) - 1,
        "mode": "classical_path",
        "total_distance_km": 0.0,
        "total_latency_ms": 0.0,
        "success": True,   # degrade on failures
        "lost_hop": None,
    }

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G.edges[u, v]
        success, m = simulate_classical_hop(edge_data)
        metrics["total_distance_km"] += m["distance_km"]
        metrics["total_latency_ms"] += m["latency_ms"]
        if not success and metrics["success"]:
            metrics["success"] = False
            metrics["lost_hop"] = (u, v)

    return metrics


# -----------------------------------------------------------
# Monte Carlo comparison
# -----------------------------------------------------------
def monte_carlo_compare(
    G: nx.Graph,
    path: List[int],
    trials: int = config.DEFAULT_MONTE_TRIALS,
) -> pd.DataFrame:
    """
    Run repeated trials for both quantum & classical (separately).
    Returns tidy DataFrame with trial-level results.
    """
    records = []
    for t in range(trials):
        q = simulate_path_quantum(G, path)
        c = simulate_path_classical(G, path)
        q["trial"] = t
        c["trial"] = t
        records.append(q)
        records.append(c)
    return pd.DataFrame.from_records(records)
