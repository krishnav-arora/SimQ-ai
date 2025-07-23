"""
Milestone 2 demo: stochastic link physics & Monte Carlo comparison.
Run: python backend/app/milestone2_sim.py
"""

import random
import argparse
import networkx as nx
import matplotlib.pyplot as plt


     # absolute import
from . import config

from .network_builder import build_hybrid_graph
from .simulator import monte_carlo_compare


def _pick_connected_pair(G: nx.Graph, rng):
    nodes = list(G.nodes)
    while True:
        a, b = rng.sample(nodes, 2)
        if nx.has_path(G, a, b):
            return a, b


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=config.DEFAULT_MONTE_TRIALS)
    parser.add_argument("--seed", type=int, default=config.RNG_SEED)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # Build graph
    G = build_hybrid_graph(seed=args.seed)

    # Pick a connected src-dst pair
    src, dst = _pick_connected_pair(G, rng)
    path = nx.shortest_path(G, src, dst, weight=None)  # for now unweighted

    print(f"Selected path {path} from {src} to {dst}.")

    # Run MC
    df = monte_carlo_compare(G, path, trials=args.trials)

    # Aggregate
    agg = (
        df.groupby("mode")
        .agg(success_rate=("success", "mean"), avg_hops=("hops", "mean"),
             avg_distance_km=("total_distance_km", "mean"))
        .reset_index()
    )
    print("\n=== Summary ===")
    print(agg.to_string(index=False))

    # Quick bar plot
    plt.figure()
    plt.bar(agg["mode"], agg["success_rate"])
    plt.ylabel("Success Probability")
    plt.ylim(0, 1)
    plt.title("Quantum vs Classical Success Rate (Milestone 2)")
    plt.show()


if __name__ == "__main__":
    main()
