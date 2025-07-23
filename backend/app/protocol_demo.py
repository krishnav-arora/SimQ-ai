"""
Protocol‑demo: shows composite‑cost path + live fallback
"""

from backend.app.network_builder import build_hybrid_graph
from backend.app.routing import send_message_reliable
import random, networkx as nx

def pick_pair(G, rng):
    nodes = list(G.nodes)
    while True:
        a, b = rng.sample(nodes, 2)
        if nx.has_path(G, a, b):
            return a, b

def main():
    G   = build_hybrid_graph(seed=123, num_nodes=15, quantum_ratio=0.4)
    src, dst = pick_pair(G, random.Random(123))
    print(f"src={src} dst={dst}")

    res = send_message_reliable(G, src, dst)
    print(res)

if __name__ == "__main__":
    main()
