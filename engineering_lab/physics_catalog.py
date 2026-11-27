"""Fixed reviewed physics experiments, distinct from runtime game code."""
from . import physics_core, physics_tyre, physics_aero

def specs(criterion):
    return {"physics_foundation":physics_core.spec(criterion),"physics_tyre":physics_tyre.spec(criterion),"physics_aero":physics_aero.spec(criterion)}
