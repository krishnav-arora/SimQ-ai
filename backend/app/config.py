"""
Centralized simulation parameters for QuasarFabric Milestone 2.
TUNE FREELY during hackathon demos!
All values are *modeling placeholders* (not hardware-accurate).
"""

# --- Quantum link params ---
# Characteristic length scale for decoherence / photon loss in fiber (km).
# Higher => more reliable long links.
COHERENCE_LENGTH_KM = 50.0

# Baseline swap success probability at a node that can perform entanglement swapping.
# (We’ll multiply this into per-hop survival when simulating chained entanglement.)
ENTANGLEMENT_SWAP_SUCCESS = 0.85

# Probability penalty when a quantum signal passes through a non-quantum (classical) node:
# used to model "no-cloning" / incompatible handling.
CLASSICAL_INTERCEPT_QUANTUM_FAIL_PROB = 0.5  # fail hard for now

# --- Classical link params ---
BASE_CLASSICAL_PACKET_LOSS = 0.01      # 1%
CONGESTION_NOISE_STD = 0.02            # add N(0,σ) clipped to [0,1]
BASE_LATENCY_MS_PER_KM = 0.005         # ~5µs/km => 0.005ms/km (rough fiber-ish speed)
JITTER_MS_STD = 0.2                    # random jitter per hop

TRANSLATION_DELAY_MS = 2.0   # cost at each quantum↔classical boundary

# --- Simulation ---
DEFAULT_MONTE_TRIALS = 1000            # number of per-scenario attempts
RNG_SEED = 42                          # reproducibility; change for variety
