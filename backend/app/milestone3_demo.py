from backend.app.network_builder import build_hybrid_graph
from backend.app.routing import send_message
from backend.app.llm_policy_builder import create_policy_from_prompt
import random, networkx as nx

def pick_connected(G):
    nodes = list(G.nodes)
    rng   = random.Random(42)
    while True:
        src, dst = rng.sample(nodes, 2)
        if nx.has_path(G, src, dst):
            return src, dst

def main():
    G   = build_hybrid_graph(seed=99)
    src, dst = pick_connected(G)
    print("src=",src,"dst=",dst)

    print("Hybrid →", send_message(G, src, dst, "hybrid"))

    prompt = (
    "Route must use only quantum‑capable edges; "
    "if impossible,fall back to shortest classical distance."
)
    create_policy_from_prompt(prompt, name="judge_policy")
    print("Judge  →", send_message(G, src, dst, "judge_policy"))

if __name__ == "__main__":
    main()
