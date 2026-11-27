"""Fixed reviewed physics experiments, distinct from runtime game code."""
from . import physics_core, physics_tyre, physics_aero, physics_powertrain, physics_brakes

def specs(criterion):
    return {"physics_foundation":physics_core.spec(criterion),"physics_tyre":physics_tyre.spec(criterion),"physics_aero":physics_aero.spec(criterion),"physics_powertrain":physics_powertrain.spec(criterion),"physics_brakes":physics_brakes.spec(criterion)}
