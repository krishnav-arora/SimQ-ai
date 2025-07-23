"""
Gymnasium‑style environment for placing ≤ K repeaters
into a hybrid graph to maximise quantum success probability.

• Observation  : binary mask (length = |V|) — 1 if node is a repeater.
• Action space : Discrete(|V|) — toggle node i (on/off).
• Reward       : quantum success rate over N trials minus a small penalty
                 for each repeater installed.
"""

import gymnasium as gym
import numpy as np
import networkx as nx
from typing import Tuple

from .network_builder import build_hybrid_graph
from .simulator import simulate_path_quantum


class RepeaterEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        G: nx.Graph | None = None,
        src: int | None = None,
        dst: int | None = None,
        max_repeaters: int = 3,
        trials: int = 200,
        seed: int = 42,
    ):
        super().__init__()
        self.rng = np.random.default_rng(seed)
        self.G_orig = G or build_hybrid_graph(seed=seed)

        self.src = src if src is not None else self.rng.integers(0, len(self.G_orig))
        self.dst = dst if dst is not None else self.rng.integers(0, len(self.G_orig))
        while self.dst == self.src:
            self.dst = self.rng.integers(0, len(self.G_orig))

        self.max_repeaters = max_repeaters
        self.trials = trials

        self.action_space = gym.spaces.Discrete(len(self.G_orig))   # toggle node i
        self.observation_space = gym.spaces.MultiBinary(len(self.G_orig))

        self.reset()

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _clone_graph(self) -> nx.Graph:
        """Return a copy of the graph with repeater upgrades applied."""
        G = self.G_orig.copy()
        for n in range(len(self.repeaters)):
            if self.repeaters[n]:
                G.nodes[n]["quantum"] = True
                G.nodes[n]["can_store_entanglement"] = True
        return G

    def _compute_reward(self) -> float:
        """Monte‑Carlo estimate of quantum success probability minus penalty."""
        G = self._clone_graph()
        try:
            path = nx.shortest_path(G, self.src, self.dst)
        except nx.NetworkXNoPath:
            return -1.0  # no connectivity at all

        successes = 0
        for _ in range(self.trials):
            metrics = simulate_path_quantum(G, path)
            successes += int(metrics["success"])

        prob_success = successes / self.trials
        penalty = 0.01 * self.repeaters.sum()
        return prob_success - penalty

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------
    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        self.repeaters = np.zeros(len(self.G_orig), dtype=np.int8)
        observation = self.repeaters.copy()
        return observation, {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Toggle repeater at node `action`.
        Episode is one step (hill‑climb style), so `done` is always True.
        """
        # toggle
        self.repeaters[action] ^= 1

        if self.repeaters.sum() > self.max_repeaters:
            # invalid move – exceed budget; undo and penalise
            self.repeaters[action] ^= 1
            reward = -0.5
        else:
            reward = self._compute_reward()

        done = True
        truncated = False
        info = {}

        return self.repeaters.copy(), reward, done, truncated, info
