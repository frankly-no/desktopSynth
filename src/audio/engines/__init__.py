from .base import SynthEngine
from .fm import FMEngine
from .vector import VectorEngine
from .subtractive import SubtractiveEngine

ENGINE_CLASSES = {
    "fm": FMEngine,
    "vector": VectorEngine,
    "subtractive": SubtractiveEngine,
}

ENGINE_NAMES = list(ENGINE_CLASSES.keys())


def make_engine(name: str) -> SynthEngine:
    cls = ENGINE_CLASSES.get(name, FMEngine)
    return cls()
