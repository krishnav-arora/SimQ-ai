"""
Global store for routing strategies.
"""

POLICIES = {}

def register(name):
    def _wrap(fn):
        POLICIES[name] = fn
        return fn
    return _wrap

def get(name):
    return POLICIES[name]