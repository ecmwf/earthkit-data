from .dim import ENS_KEYS
from .dim import Dim
from .dim import DimBuilder
from .dim import get_keys


class NumberDim(Dim):
    alias = get_keys(ENS_KEYS)


class NumberDimBuilder(DimBuilder):
    name = "number"

    def __init__(self, profile, owner, **kwargs):
        key, name = owner.dim_roles.role("number")
        self.used = {self.name: NumberDim(owner, name=name, key=key)}


PREDEFINED_DIMS = [NumberDim]
