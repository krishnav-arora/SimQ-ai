import networkx as nx, random
from backend.app.network_builder import build_hybrid_graph
from backend.app.routing           import send_message
from backend.app.llm_policy_builder import create_policy_from_prompt

def build_special_graph(seed=2025):
    """
    Build a graph where:
      • Nodes 0‑11
      • A long quantum‑only corridor 0‑1‑2‑3‑4‑5
      • A short classical shortcut 0‑10‑11‑5
    """
    rng = random.Random(seed)
    G = nx.Graph()

    # add 12 nodes, mark 0‑5 as quantum, 6‑11 as classical
    for n in range(12):
        G.add_node(n, quantum=(n <= 5), can_store_entanglement=(n <= 5))

    # Long quantum chain 0‑1‑2‑3‑4‑5 (all 50 km edges)
    for u, v in zip(range(6), range(1, 6)):
        G.add_edge(u, v, quantum=True,  distance_km=50)

    # Classical shortcut 0‑10‑11‑5 (all 10 km edges)
    G.add_node(10, quantum=False); G.add_node(11, quantum=False)
    G.add_edge(0, 10, quantum=False, distance_km=10)
    G.add_edge(10, 11, quantum=False, distance_km=10)
    G.add_edge(11, 5,  quantum=False, distance_km=10)

    # sprinkle a few extra random classical links so the graph stays connected
    for _ in range(10):
        a, b = rng.sample(range(12), 2)
        if not G.has_edge(a, b):
            G.add_edge(a, b, quantum=False,
                       distance_km=rng.uniform(20, 120))
    return G

def main():
    G   = build_special_graph()
    src, dst = 0, 5                  # opposite ends of the corridor

    # built‑in hybrid
    print("Hybrid  ->", send_message(G, src, dst, "hybrid"))

    # LLM policy: quantum‑only else shortest classical
    prompt = (
    "Use only classical (non‑quantum) edges if a path exists; "
    "if no classical‑only path exists, fall back to the shortest total distance."
)
    create_policy_from_prompt(prompt, name="judge_policy")
    print("Judge   ->", send_message(G, src, dst, "judge_policy"))

if __name__ == "__main__":
    main()
