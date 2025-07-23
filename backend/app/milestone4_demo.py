"""
Milestone 4 demo:
  • Create env on same graph as Milestone 2
  • Run hill‑climb
  • Print before/after quantum success rates
"""

import networkx as nx
import matplotlib.pyplot as plt
from backend.app.network_builder import build_hybrid_graph
from backend.app.repeater_env import RepeaterEnv
from backend.app.repeater_agent import hill_climb

def plot_graph(G, repeaters_mask, title):
    pos = nx.spring_layout(G, seed=42)
    node_colors = []
    for i, data in G.nodes(data=True):
        if repeaters_mask[i]:
            node_colors.append("#00c853")        # bright green for repeater
        elif data["quantum"]:
            node_colors.append("#8E7BF1")        # purple
        else:
            node_colors.append("#C4C4C4")        # gray
    edge_colors = ["#FF6B00" if d["quantum"] else "#AAAAAA" for _,_,d in G.edges(data=True)]
    nx.draw(G, pos, node_color=node_colors, edge_color=edge_colors, with_labels=True, node_size=600)
    plt.title(title)

def main():
    G = build_hybrid_graph(seed=123)
    env = RepeaterEnv(G=G, max_repeaters=3, trials=300)
    before = env._compute_reward()
    print(f"Initial quantum success minus penalty ≈ {before:.2f}")

    mask, after = hill_climb(env, iterations=1500)
    print(f"After placing repeaters @ {list(np.where(mask==1)[0])} → score ≈ {after:.2f}")

    plt.figure(figsize=(10,4))
    plt.subplot(1,2,1)
    plot_graph(G, repeaters_mask=np.zeros(len(G), dtype=int), title="Before")
    plt.subplot(1,2,2)
    plot_graph(G, repeaters_mask=mask, title="After (with repeaters)")
    plt.show()

if __name__ == "__main__":
    import numpy as np
    main()
