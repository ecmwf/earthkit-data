# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import inspect

NO_CARTOPY = False
try:
    import cartopy.crs as ccrs
except ImportError:
    NO_CARTOPY = True


class CFParameters:
    """
    Class for mapping CF-compliant grid mappings to cartopy CRS arguments.

    Parameter mappings are based on the CF Grid Mappings specification at
    https://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/build/apf.html
    """

    def __init__(self, **kwargs):
        self.params = kwargs

    def __getattr__(self, attr):
        if attr in self.params:
            return self.params[attr]
        else:
            return super().__getattr__(attr)

    @property
    def central_latitude(self):
        return self.params.get("latitude_of_projection_origin")

    @property
    def central_longitude(self):
        return self.params.get(
            "longitude_of_central_meridian",
            self.params.get("longitude_of_projection_origin"),
        )

    @property
    def pole_latitude(self):
        return self.params.get("grid_north_pole_latitude")

    @property
    def pole_longitude(self):
        return self.params.get("grid_north_pole_longitude")

    @property
    def central_rotated_longitude(self):
        return self.params.get("north_pole_grid_longitude")

    @property
    def satellite_height(self):
        return self.params.get("perspective_point_height")

    @property
    def scale_factor(self):
        return self.params.get(
            "scale_factor_at_projection_origin",
            self.params.get("scale_factor_at_central_meridian"),
        )

    @property
    def standard_parallels(self):
        value = self.params.get("standard_parallel")

        # cartopy expects standard parallels to always be iterable
        if value is not None:
            value = [value] if not isinstance(value, (list, tuple)) else value

        return value


class CFGridMapping:
    GRID_MAPPING_NAME = None

    @classmethod
    def from_grid_mapping(cls, grid_mapping_name, **kwargs):
        for kls in _CF_GRID_MAPPINGS:
            if grid_mapping_name == kls.GRID_MAPPING_NAME:
                break
        else:
            raise ValueError(f"invalid CF grid mapping '{grid_mapping_name}'")

        return kls(**kwargs)

    def __init__(self, **kwargs):
        if NO_CARTOPY:
            raise ImportError(
                "no cartopy installation found; cartopy must be installed to "
                "use this feature"
            )
        self.cf_parameters = CFParameters(**kwargs)

    @property
    def _ccrs_class(self):
        crs_name = self.__class__.__name__
        if hasattr(ccrs, crs_name):
            return getattr(ccrs, crs_name)
        else:
            raise ValueError(f"cartopy has no crs {crs_name}")

    @property
    def _ccrs_kwargs(self):
        crs_kwargs = dict()
        for param in inspect.signature(self._ccrs_class).parameters:
            try:
                value = getattr(self.cf_parameters, param)
            except AttributeError:
                continue
            else:
                if value is not None:
                    crs_kwargs[param] = value
        return crs_kwargs

    def to_ccrs(self):
        return self._ccrs_class(**self._ccrs_kwargs)


class AlbersEqualArea(CFGridMapping):
    GRID_MAPPING_NAME = "albers_conic_equal_area"


class AzimuthalEquidistant(CFGridMapping):
    GRID_MAPPING_NAME = "azimuthal_equidistant"


class LambertAzimuthalEqualArea(CFGridMapping):
    GRID_MAPPING_NAME = "lambert_azimuthal_equal_area"


class LambertConformal(CFGridMapping):
    GRID_MAPPING_NAME = "lambert_conformal_conic"


class LambertCylindrical(CFGridMapping):
    GRID_MAPPING_NAME = "lambert_cylindrical_equal_area"


class PlateCarree(CFGridMapping):
    GRID_MAPPING_NAME = "latitude_longitude"


class Mercator(CFGridMapping):
    GRID_MAPPING_NAME = "mercator"


class Orthographic(CFGridMapping):
    GRID_MAPPING_NAME = "orthographic"


class PolarStereographic(CFGridMapping):
    GRID_MAPPING_NAME = "polar_stereographic"

    def __init__(self, *args, **kwargs):
        raise NotImplementedError()


class RotatedPole(CFGridMapping):
    GRID_MAPPING_NAME = "rotated_latitude_longitude"


class Stereographic(CFGridMapping):
    GRID_MAPPING_NAME = "stereographic"


class TransverseMercator(CFGridMapping):
    GRID_MAPPING_NAME = "transverse_mercator"


class NearsidePerspective(CFGridMapping):
    GRID_MAPPING_NAME = "vertical_perspective"


_CF_GRID_MAPPINGS = [
    AlbersEqualArea,
    AzimuthalEquidistant,
    LambertAzimuthalEqualArea,
    LambertConformal,
    LambertCylindrical,
    PlateCarree,
    Mercator,
    Orthographic,
    PolarStereographic,
    RotatedPole,
    Stereographic,
    TransverseMercator,
    NearsidePerspective,
]
