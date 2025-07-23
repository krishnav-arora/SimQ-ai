"""
Routing engine for HybridNet.

Contents
~~~~~~~~
1.  Edge‑cost helpers
2.  Policy registry + three default policies
3.  send_message()           – simple hybrid quantum → classical fallback
4.  send_message_reliable()  – quantum → classical (same) → classical (alt)
    *returns a `history` list so UIs can display every attempt*
"""

from __future__ import annotations
import math
from typing import List, Dict, Any

import networkx as nx

from backend.policy_registry import register, get as get_policy
from backend.app.simulator import (
    simulate_path_quantum,
    simulate_path_classical,
)
# ----------------------------------------------------------------------
# 1. Edge‑cost helper functions
# ----------------------------------------------------------------------
def quantum_survival_prob(dist_km: float, L=50.0) -> float:
    """Toy decoherence model: P = exp(−d/L)."""
    import math
    return math.exp(-dist_km / L)

def q_weight(dist_km: float) -> float:
    """Cost = −log(P).  Lower is better."""
    p = quantum_survival_prob(dist_km)
    return -math.log(max(p, 1e-9))

def c_latency_weight(dist_km: float) -> float:
    """Classical latency proxy in ms."""
    return dist_km * 0.005  # 5 µs per km


# ----------------------------------------------------------------------
# 2. Policy registry + defaults
# ----------------------------------------------------------------------
@register("quantum_only")
def quantum_only(G: nx.Graph, src: int, dst: int) -> List[int] | None:
    sub = G.edge_subgraph([(u, v) for u, v, d in G.edges(data=True) if d["quantum"]]).copy()
    if src not in sub or dst not in sub or not nx.has_path(sub, src, dst):
        return None
    return nx.shortest_path(sub, src, dst, weight=lambda u, v, d: q_weight(d["distance_km"]))

@register("classical_latency")
def classical_latency(G: nx.Graph, src: int, dst: int) -> List[int] | None:
    try:
        return nx.shortest_path(G, src, dst, weight=lambda u, v, d: c_latency_weight(d["distance_km"]))
    except nx.NetworkXNoPath:
        return None

@register("hybrid")
def hybrid(G: nx.Graph, src: int, dst: int) -> List[int]:
    """
    Greedy reliability‑aware hybrid:

    • While a quantum‑only path exists from current → dst, take the FIRST hop
      of that quantum path (lowest latency cost).
    • Simulate that single‑hop quantum transmission.  If it fails, switch to
      best classical‑latency path from the *current node* to dst.
    • Result is a mixed (quantum‑then‑classical) path.  Works even when no
      complete quantum path exists ahead of time.
    """
    path: List[int] = [src]
    here = src
    while here != dst:
        # try to find a quantum‑only path from 'here' to dst
        try:
            Q = nx.Graph((u, v, d) for u, v, d in G.edges(data=True) if d["quantum"])
            qpath = nx.shortest_path(Q, here, dst, weight=lambda u,v,d: q_weight(d["distance_km"]))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            qpath = None

        if qpath and len(qpath) > 1:
            # take the first quantum hop
            next_hop = qpath[1]
            path.append(next_hop)
            here = next_hop
            # defer failure handling to send_message_reliable()
        else:
            # no quantum route ⇒ append classical shortest‑latency path and stop
            c_tail = classical_latency(G, here, dst)
            if c_tail:
                path.extend(c_tail[1:])      # skip repeating 'here'
            break
    return path


# ----------------------------------------------------------------------
# 3. Simple send_message (Milestone 3)
# ----------------------------------------------------------------------
def send_message(G: nx.Graph, src: int, dst: int, policy: str = "hybrid") -> Dict[str, Any]:
    path_fn = get_policy(policy)
    path = path_fn(G, src, dst)
    if not path:
        return {"success": False, "reason": "no_path", "policy": policy}

    if simulate_path_quantum(G, path)["success"]:
        return {"success": True, "mode": "quantum", "path": path}

    success = simulate_path_classical(G, path)["success"]
    return {"success": success, "mode": "classical", "path": path}


# ----------------------------------------------------------------------
# 4. Robust send_message_reliable (with history)
# ----------------------------------------------------------------------
def _classical_latency_path(G: nx.Graph, src: int, dst: int) -> List[int] | None:
    """Shortest path weighted only by distance_km (pure classical metric)."""
    try:
        return nx.shortest_path(G, src, dst, weight="distance_km")
    except nx.NetworkXNoPath:
        return None

# ----------------------------------------------------------------------
# 4. Robust send_message_reliable (policy‑aware + hop history)
# ----------------------------------------------------------------------
def send_message_reliable(
    G: nx.Graph,
    src: int,
    dst: int,
    policy: str = "hybrid",
) -> Dict[str, Any]:
    """
    Executes the chosen policy hop‑by‑hop.
    • Records every hop with its own success flag.
    • If a quantum hop fails, switches to fastest classical path *from that node*.
    • 'mode' in the final result reflects the policy actually used.
    """
    history: List[Dict[str, Any]] = []

    # -----------------------------------------------------------
    # Helper: label the initial policy mode
    # -----------------------------------------------------------
    mode_lookup = {
        "quantum_only":        "quantum_path",
        "classical_latency":   "classical_path",
        "hybrid":              "hybrid_path",
    }
    init_mode = mode_lookup.get(policy, policy)

    # -----------------------------------------------------------
    # Build initial path
    # -----------------------------------------------------------
    path_fn = globals().get(policy, hybrid)
    full_path = path_fn(G, src, dst)
    if not full_path or len(full_path) < 2:
        return {"success": False, "reason": "no_path", "history": history}

    # -----------------------------------------------------------
    # Walk hop by hop
    # -----------------------------------------------------------
    assembled: List[int] = [full_path[0]]
    for u, v in zip(full_path, full_path[1:]):
        edge_path = [u, v]
        d = G.edges[u, v]

        if d["quantum"]:
            qres = simulate_path_quantum(G, edge_path)
            history.append({"mode": "quantum", **qres, "path": edge_path})
            if not qres["success"]:
                # Quantum hop failed → switch to classical from here
                tail = classical_latency(G, u, dst)
                if not tail:
                    return {
                        "success": False,
                        "reason": "no_classical_fallback",
                        "history": history,
                    }
                # execute classical tail
                for x, y in zip(tail, tail[1:]):
                    cres = simulate_path_classical(G, [x, y])
                    history.append({"mode": "classical", **cres, "path": [x, y]})
                assembled.extend(tail[1:])
                return {
                    "success": True,
                    "mode": init_mode,
                    "path": assembled,
                    "history": history,
                }
        else:
            cres = simulate_path_classical(G, edge_path)
            history.append({"mode": "classical", **cres, "path": edge_path})

        assembled.append(v)

    # -----------------------------------------------------------
    # All hops succeeded
    # -----------------------------------------------------------
    return {
        "success": True,
        "mode": init_mode,
        "path": assembled,
        "history": history,
    }
