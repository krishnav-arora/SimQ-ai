"""
Stochastic link-level behavior models.
Quantum: decoherence over distance, entanglement swap success.
Classical: packet loss, latency w/ jitter.
"""

from __future__ import annotations
import math
import random
from typing import Dict, Any, Tuple

from . import config


_rng = random.Random(config.RNG_SEED)


# -----------------------------
# Quantum link survival
# -----------------------------
def quantum_survival_prob(distance_km: float) -> float:
    """
    Toy exponential attenuation model:
    P = exp(-d / L)  where L = config.COHERENCE_LENGTH_KM.
    Clipped to [0,1].
    """
    L = config.COHERENCE_LENGTH_KM
    p = math.exp(-distance_km / L)
    return max(0.0, min(1.0, p))


def simulate_quantum_hop(edge_data: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
    """
    Simulate transmitting a qubit / entangled photon pair across a single edge.
    Returns (success, metrics_dict).
    Edge must include:
        distance_km: float
        quantum: bool   (if False, classical node intercept => fail)
    """
    dist = float(edge_data["distance_km"])
    if not edge_data.get("quantum", False):
        # We "attempted" a quantum transmission over a non-quantum edge -> violates model
        fail_prob = config.CLASSICAL_INTERCEPT_QUANTUM_FAIL_PROB
        success = _rng.random() > fail_prob
        return success, {"p_survive": 1 - fail_prob, "distance_km": dist, "mode": "quantum_over_classical"}

    p_survive = quantum_survival_prob(dist)
    success = _rng.random() < p_survive
    return success, {"p_survive": p_survive, "distance_km": dist, "mode": "quantum"}


# -----------------------------
# Entanglement swap at node
# -----------------------------
def simulate_entanglement_swap(can_swap: bool) -> Tuple[bool, float]:
    """
    Node-level swap success.
    """
    if not can_swap:
        return False, 0.0
    p = config.ENTANGLEMENT_SWAP_SUCCESS
    return (_rng.random() < p), p


# -----------------------------
# Classical hop
# -----------------------------
def classical_loss_prob(distance_km: float) -> float:
    """
    Base + noise, clipped.
    """
    base = config.BASE_CLASSICAL_PACKET_LOSS
    noisy = base + _rng.gauss(0.0, config.CONGESTION_NOISE_STD)
    noisy = max(0.0, min(1.0, noisy))
    return noisy


def classical_latency_ms(distance_km: float) -> float:
    # Rough fiber speed model + jitter
    base = distance_km * config.BASE_LATENCY_MS_PER_KM
    jitter = _rng.gauss(0.0, config.JITTER_MS_STD)
    return max(0.0, base + jitter)


def simulate_classical_hop(edge_data: Dict[str, Any]):
    dist = float(edge_data["distance_km"])
    p_loss = classical_loss_prob(dist)
    success = _rng.random() > p_loss
    latency = classical_latency_ms(dist)
    return success, {"p_loss": p_loss, "latency_ms": latency, "distance_km": dist, "mode": "classical"}
