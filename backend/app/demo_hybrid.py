import random
import networkx as nx
import matplotlib.pyplot as plt

# ————————————————————————————
# 1. Build topology
# ————————————————————————————
NUM_NODES = 10
quantum_ratio = 0.4        # 40 % quantum‑capable

G = nx.Graph()

for i in range(NUM_NODES):
    is_quantum = random.random() < quantum_ratio
    G.add_node(
        i,
        quantum=is_quantum,
        can_store_entanglement=is_quantum and random.random() < 0.6,
    )

# Random edges (sparse)
for i in range(NUM_NODES):
    for j in range(i + 1, NUM_NODES):
        if random.random() < 0.3:
            is_quantum_link = G.nodes[i]["quantum"] and G.nodes[j]["quantum"]
            G.add_edge(i, j, quantum=is_quantum_link)

# ————————————————————————————
# 2. Visualise with Labels
# ————————————————————————————
pos = nx.spring_layout(G, seed=42)

node_colors = [
    "#8E7BF1" if data["quantum"] else "#C4C4C4"
    for _, data in G.nodes(data=True)
]

edge_colors = [
    "#FF6B00" if data["quantum"] else "#AAAAAA"
    for _, _, data in G.edges(data=True)
]

# Add custom labels: "Q" or "C"
labels = {
    node: f"{node} ({'Q' if data['quantum'] else 'C'})"
    for node, data in G.nodes(data=True)
}

nx.draw(
    G, pos,
    with_labels=False,
    node_color=node_colors,
    edge_color=edge_colors,
    node_size=700,
    width=2
)

# Draw custom labels
nx.draw_networkx_labels(G, pos, labels=labels, font_size=9)

plt.title("Hybrid Quantum‑Classical Network (Labeled)")
plt.show()
