from .dim import LEVEL_KEYS
from .dim import LEVEL_TYPE_KEYS
from .dim import Dim
from .dim import DimBuilder
from .dim import DimMode
from .dim import get_keys


class LevelDim(Dim):
    alias = get_keys(LEVEL_KEYS)


class LevelTypeDim(Dim):
    alias = get_keys(LEVEL_TYPE_KEYS)
    enforce_unique = True


class LevelPerTypeDim(Dim):
    name = "_level_per_type"
    drop = get_keys(LEVEL_KEYS + LEVEL_TYPE_KEYS, drop=name)

    def __init__(self, owner, level_key, level_type_key, *args, **kwargs):
        self.key = level_key
        self.level_key = level_key
        self.level_type_key = level_type_key
        super().__init__(owner, *args, **kwargs)

    def as_coord(self, key, values, component, source):
        lev_type = source[0].metadata(self.level_type_key)
        if not lev_type:
            raise ValueError(f"{self.level_type_key} not found in metadata")

        if lev_type not in self.coords:
            from .coord import Coord

            coord = Coord.make(lev_type, list(values), ds=source)
            self.coords[lev_type] = coord
        return lev_type, self.coords[lev_type]


class LevelAndTypeDim(Dim):
    name = "level_and_type"
    drop = get_keys(LEVEL_KEYS + LEVEL_TYPE_KEYS, drop=name)

    def __init__(self, owner, level_key, level_type_key, active=True, *args, **kwargs):
        self.level_key = level_key
        self.level_type_key = level_type_key
        if active:
            owner.register_remapping(
                {self.name: "{" + self.level_key + "}{" + self.level_type_key + "}"},
            )
        super().__init__(owner, *args, active=active, **kwargs)

    def remapping_keys(self):
        return [self.level_key, self.level_type_key]


class LevelDimMode(DimMode):
    name = "level"

    def build(self, profile, owner, **kwargs):
        # level
        key, name = owner.dim_roles.role("level")
        level_dim = LevelDim(owner, name=name, key=key, **kwargs)

        # level_type
        key, name = owner.dim_roles.role("level_type")
        level_type_dim = LevelTypeDim(owner, name=name, key=key, **kwargs)

        return {level_dim.key: level_dim, level_type_dim.key: level_type_dim}


class LevelAndTypeDimMode(DimMode):
    name = "level_and_type"
    dim = LevelAndTypeDim

    def build(self, profile, owner, **kwargs):

        level_key, _ = owner.dim_roles.role("level")
        level_type_key, _ = owner.dim_roles.role("level_type")
        return {self.name: self.dim(owner, level_key, level_type_key, **kwargs)}


class LevelPerTypeDimMode(LevelAndTypeDimMode):
    name = "level_per_type"
    dim = LevelPerTypeDim


# TIME_DIM_MODES = {v.name: v for v in [ForecastTimeDimMode, ValidTimeDimMode, RawTimeDimMode]}
LEVEL_DIM_MODES = {v.name: v for v in [LevelDimMode, LevelPerTypeDimMode, LevelAndTypeDimMode]}


class LevelDimBuilder(DimBuilder):
    name = "level"

    def __init__(self, profile, owner, **kwargs):
        mode = LEVEL_DIM_MODES.get(owner.level_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown level_dim_mode={owner.level_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in LEVEL_DIM_MODES.items() if v != mode
        }


PREDEFINED_DIMS = [
    LevelDim,
    LevelPerTypeDim,
    LevelAndTypeDim,
]
