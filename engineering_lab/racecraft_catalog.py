"""Fixed isolated Racecraft research experiments."""
from . import racecraft_core, racecraft_space

def specs(criterion):
    return {"racecraft_foundation":racecraft_core.spec(criterion),"racecraft_spatial_awareness":racecraft_space.spec(criterion)}
