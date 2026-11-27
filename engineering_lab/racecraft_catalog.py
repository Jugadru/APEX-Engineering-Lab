"""Fixed isolated Racecraft research experiments."""
from . import racecraft_core, racecraft_space, racecraft_trajectory, racecraft_attack, racecraft_defense

def specs(criterion):
    return {"racecraft_foundation":racecraft_core.spec(criterion),"racecraft_spatial_awareness":racecraft_space.spec(criterion),"racecraft_trajectory":racecraft_trajectory.spec(criterion),"racecraft_overtaking":racecraft_attack.spec(criterion),"racecraft_defensive":racecraft_defense.spec(criterion)}
