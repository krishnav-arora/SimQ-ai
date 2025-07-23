"""
Build annotated hybrid graphs for simulation.
"""

import random
from typing import Tuple
import networkx as nx

def build_hybrid_graph(
    num_nodes: int = 10,
    quantum_ratio: float = 0.4,
    edge_prob: float = 0.3,
    dist_range_km: Tuple[float, float] = (5.0, 200.0),
    seed: int = 42,
) -> nx.Graph:
    rng = random.Random(seed)
    G = nx.Graph()

    # Nodes
    for i in range(num_nodes):
        is_quantum = rng.random() < quantum_ratio
        G.add_node(
            i,
            quantum=is_quantum,
            can_store_entanglement=is_quantum and rng.random() < 0.6,
        )

    # Edges
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if rng.random() < edge_prob:
                dist = rng.uniform(*dist_range_km)
                is_quantum_link = G.nodes[i]["quantum"] and G.nodes[j]["quantum"]
                G.add_edge(
                    i,
                    j,
                    quantum=is_quantum_link,
                    distance_km=round(dist, 2),
                )

    return G
