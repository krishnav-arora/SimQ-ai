"""
Greedy stochastic hill‑climber:
    • Start with zero repeaters
    • Evaluate reward
    • Randomly flip a node; keep change iff reward improves
Repeat for N iterations.
"""

import numpy as np
from tqdm import trange
from .repeater_env import RepeaterEnv

def hill_climb(env: RepeaterEnv, iterations: int = 1000):
    obs, _ = env.reset()
    best_reward = env._compute_reward()
    best_mask = obs.copy()

    for _ in trange(iterations, desc="hill‑climb", leave=False):
        candidate = best_mask.copy()
        flip = env.rng.integers(0, len(candidate))
        candidate[flip] ^= 1
        env.repeaters = candidate
        if candidate.sum() > env.max_repeaters:
            continue
        reward = env._compute_reward()
        if reward > best_reward:
            best_reward = reward
            best_mask = candidate.copy()
    # set env to best
    env.repeaters = best_mask
    final_reward = best_reward
    return best_mask, final_reward
