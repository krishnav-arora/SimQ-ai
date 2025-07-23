"""
Local LLM co‑pilot using Ollama (offline, no internet).
Turns plain‑English routing rules into a live Python policy.

Key features
• Few‑shot template so the model always returns syntactically correct code.
• Strips any stray markdown fences/back‑ticks.
• Renames the first function to CUSTOM() and self‑tests it.
• Retries up to MAX_RETRY times, then falls back to a heuristic.
"""

from __future__ import annotations
import os, re, textwrap, ast, networkx as nx, ollama
from backend.policy_registry import register

MODEL      = os.getenv("OLLAMA_MODEL", "llama3:8b")  # model tag you pulled
MAX_RETRY  = 3                                       # ask LLM at most N times
NPREDICT   = 512                                     # prevent truncation

# ------------------------------------------------------------------ #
# 1. Chat helper                                                     #
# ------------------------------------------------------------------ #
def _ask_llm(policy_prompt: str) -> str:
    """One big prompt so small models stay on‑track."""
    template = f"""
### TASK
Write a Python function named CUSTOM(G, src, dst) that returns a list of
node indices (a path).  Only use the 'networkx' API, already imported as 'nx'.

### EXAMPLE STRUCTURE (imitate this pattern)
def CUSTOM(G, src, dst):
    # 1. Try a quantum‑only path first
    try:
        sub = G.edge_subgraph(
            [(u, v) for u, v, d in G.edges(data=True) if d.get("quantum")]
        ).copy()
        if src in sub and dst in sub:
            return nx.shortest_path(sub, src, dst)
    except nx.NetworkXNoPath:
        pass  # fall through

    # 2. Fallback: classical shortest distance
    return nx.shortest_path(G, src, dst, weight="distance_km")

### USER RULES
{policy_prompt}

### NOW OUTPUT ONLY THE CODE (NO MARKDOWN) BELOW
"""
    return ollama.chat(
        model    = MODEL,
        messages = [{"role": "user", "content": template}],
        options  = {"temperature": 0.2, "num_predict": NPREDICT},
    )["message"]["content"]

# ------------------------------------------------------------------ #
# 2.  Clean & rename                                                 #
# ------------------------------------------------------------------ #
def _clean_code(raw: str) -> str:
    """Strip all ``` fences/back‑ticks & dedent."""
    code = re.sub(r"```(?:python)?", "", raw)
    code = code.replace("```", "").replace("`", "")
    return textwrap.dedent(code).strip()

def _rename_first_def(code: str) -> str:
    """Ensure the first def is called CUSTOM."""
    try:
        module = ast.parse(code)
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name != "CUSTOM":
                code = re.sub(
                    rf"\bdef\s+{re.escape(node.name)}\b",
                    "def CUSTOM",
                    code,
                    count=1,
                )
                break
    except SyntaxError:
        pass
    return code

# ------------------------------------------------------------------ #
# 3.  Compile & quick self‑test                                      #
# ------------------------------------------------------------------ #
def _compile(code: str):
    env = {"nx": nx, "__builtins__": __builtins__}
    ns  = {}
    exec(code, env, ns)                       # may raise SyntaxError
    fn = ns.get("CUSTOM")
    if not callable(fn):
        raise ValueError("Function CUSTOM not defined.")
    # self‑test on a trivial graph
    G_test = nx.Graph()
    G_test.add_edge(0, 1, quantum=True, distance_km=10)
    fn(G_test, 0, 1)                          # may raise NameError
    return fn

# ------------------------------------------------------------------ #
# 4.  Public entry point                                             #
# ------------------------------------------------------------------ #
def create_policy_from_prompt(prompt: str, name: str = "custom"):
    """
    Register a new routing policy from an English description.
    Retries, sanitises, and falls back to a heuristic on failure.
    """
    for attempt in range(1, MAX_RETRY + 1):
        try:
            raw  = _ask_llm(prompt)
            code = _rename_first_def(_clean_code(raw))
            fn   = _compile(code)
            register(name)(fn)
            return fn
        except Exception as err:
            print(f"[LLM retry {attempt}/{MAX_RETRY}] {err}")

    # ---- fallback heuristic ---------------------------------------
    def heuristic(G, src, dst):
        weight = "distance_km" if "distance" in prompt.lower() else None
        return nx.shortest_path(G, src, dst, weight=weight)

    register(name)(heuristic)
    return heuristic
