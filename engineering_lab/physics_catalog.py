"""Fixed reviewed physics experiments, distinct from runtime game code."""
from . import physics_core

def specs(criterion):
    return {"physics_foundation":physics_core.spec(criterion)}
