"""Fixed isolated Racecraft research experiments."""
from . import racecraft_core

def specs(criterion):
    return {"racecraft_foundation":racecraft_core.spec(criterion)}
