"""
Generate Part‑2 report plots:

1. Quantum decoherence curve.
2. Quantum vs classical success rate as network size grows.
3. Classical end‑to‑end latency CDF.

Run:
    python -m backend.app.plot_link_behavior
"""

import numpy as np, matplotlib.pyplot as plt, os, networkx as nx, random
from tqdm import tqdm

from backend.app.link_models   import quantum_survival_prob
from backend.app.network_builder import build_hybrid_graph
from backend.app.simulator     import simulate_path_quantum, simulate_path_classical

PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ------------------------------------------------------------------ #
# 1. Decoherence curve                                               #
# ------------------------------------------------------------------ #
d_km = np.linspace(0, 300, 301)
survival = [quantum_survival_prob(d) for d in d_km]

plt.figure()
plt.plot(d_km, survival)
plt.xlabel("Distance (km)")
plt.ylabel("Quantum survival probability")
plt.title("Decoherence vs distance")
plt.grid(True, alpha=0.3)
plt.savefig(f"{PLOT_DIR}/decoherence_curve.png", dpi=150)
plt.close()


# ------------------------------------------------------------------ #
# 2. Success rate vs network size                                    #
# ------------------------------------------------------------------ #
# ------------------------------------------------------------------ #
# 2. Success‑rate, hop‑count, composite‑cost vs network size         #
# ------------------------------------------------------------------ #
sizes       = [10, 50, 100, 200]
q_rates     = []
c_rates     = []
hop_avgs    = []
cost_avgs   = []

def composite_cost(G, path, α=1.0, β=1.0, γ=1.0):
    cost = 0.0
    for u, v in zip(path, path[1:]):
        d     = G.edges[u, v]
        hops  = 1
        lat   = d["distance_km"] * 0.005
        qcost = 0.0 if not d["quantum"] else d["distance_km"] / 50.0
        cost += α*hops + β*lat + γ*qcost
    return cost

for n in tqdm(sizes, desc="network size sweep"):
    G   = build_hybrid_graph(num_nodes=n, seed=42)
    rng = random.Random(42)

    succ_q = succ_c = total_hops = total_cost = trials = 0
    for _ in range(50):
        src, dst = rng.sample(list(G.nodes), 2)
        if not nx.has_path(G, src, dst):
            continue
        path = nx.shortest_path(G, src, dst)
        trials += 1
        total_hops += len(path) - 1
        total_cost += composite_cost(G, path)

        succ_q += simulate_path_quantum(G, path)["success"]
        succ_c += simulate_path_classical(G, path)["success"]

    q_rates.append(succ_q / trials)
    c_rates.append(succ_c / trials)
    hop_avgs.append(total_hops / trials)
    cost_avgs.append(total_cost / trials)

# -- Plot 1: success vs size (kept the same) ------------------------
plt.figure()
plt.plot(sizes, q_rates, "o-", label="Quantum")
plt.plot(sizes, c_rates, "s-", label="Classical")
plt.xlabel("Number of nodes")
plt.ylabel("End‑to‑end success probability")
plt.title("Success rate vs network size")
plt.legend(); plt.grid(alpha=0.3)
plt.savefig(f"{PLOT_DIR}/success_vs_size.png", dpi=150)
plt.close()

# -- Plot 2: hop‑count vs size -------------------------------------
plt.figure()
plt.plot(sizes, hop_avgs, "d-")
plt.xlabel("Number of nodes"); plt.ylabel("Avg hops")
plt.title("Average hop‑count vs network size")
plt.grid(alpha=0.3)
plt.savefig(f"{PLOT_DIR}/hopcount_vs_size.png", dpi=150)
plt.close()

# -- Plot 3: composite cost vs size --------------------------------
plt.figure()
plt.plot(sizes, cost_avgs, "^-")
plt.xlabel("Number of nodes"); plt.ylabel("Avg composite cost")
plt.title("Composite cost (α=β=γ=1) vs network size")
plt.grid(alpha=0.3)
plt.savefig(f"{PLOT_DIR}/cost_vs_size.png", dpi=150)
plt.close()
