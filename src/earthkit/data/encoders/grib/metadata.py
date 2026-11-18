# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from functools import lru_cache

from earthkit.data.utils.humanize import list_to_human

LOG = logging.getLogger(__name__)

_NOT_IN_EDITION_1 = (
    "productDefinitionTemplateNumber",
    "typeOfGeneratingProcess",
)

_COMPULSORY = (("date", "referenceDate"), ("param", "paramId", "shortName"))


@lru_cache(maxsize=None)
def _gg_pl(N):
    import eccodes

    sample = None
    result = {}
    try:
        sample = eccodes.codes_new_from_samples(
            f"reduced_gg_pl_{N}_grib2",
            eccodes.CODES_PRODUCT_GRIB,
        )

        for key in ("N", "Ni", "Nj"):
            result[key] = eccodes.codes_get(sample, key)

        for key in (
            "latitudeOfFirstGridPointInDegrees",
            "longitudeOfFirstGridPointInDegrees",
            "latitudeOfLastGridPointInDegrees",
            "longitudeOfLastGridPointInDegrees",
            "iDirectionIncrementInDegrees",
        ):
            result[key] = eccodes.codes_get_double(sample, key)

        pl = eccodes.codes_get_long_array(sample, "pl")
        result["pl"] = pl.tolist()
        result["gridType"] = "reduced_gg"

        return result

    finally:
        if sample is not None:
            eccodes.codes_release(sample)


class MetadataHandleBuilder:
    def __init__(self):
        self._bbox = {}

    def handle_from_metadata(self, values_shape, metadata, compulsory):
        from earthkit.data.readers.grib.handle import GribCodesHandle  # Lazy loading of eccodes

        if len(values_shape) == 1:
            sample = self._gg_field(values_shape, metadata)
        elif len(values_shape) == 2:
            sample = self._ll_field(values_shape, metadata)
        else:
            raise ValueError(f"Invalid shape {values_shape} for GRIB, must be 1 or 2 dimension ")

        metadata.setdefault("bitsPerValue", 16)
        metadata["scanningMode"] = 0

        if "class" in metadata or "type" in metadata or "stream" in metadata or "expver" in metadata:
            # MARS labelling
            metadata["setLocalDefinition"] = 1
            # metadata['grib2LocalSectionNumber'] = 1

        for check in compulsory:
            if not isinstance(check, tuple):
                check = [check]

            if not any(c in metadata for c in check):
                choices = list_to_human([f"'{c}'" for c in check], "or")
                raise ValueError(f"Please provide a value for {choices}.")

        LOG.debug("GribCodesHandle.from_sample(%s)", sample)
        return GribCodesHandle.from_sample(sample)

    def _levtype_from_metadata(self, metadata):
        levtype = metadata.get("levtype", None)
        type_of_level = metadata.get("typeOfLevel", None)

        if levtype is None:
            if type_of_level is not None:
                if type_of_level == "isobaricInhPa":
                    levtype = "pl"
                elif type_of_level == "surface":
                    levtype = "sfc"
                else:
                    raise ValueError(
                        f"Unsupported typeOfLevel {type_of_level} for GRIB encoding when only metadata is provided."
                    )
            elif "levelist" in metadata or "level" in metadata:
                levtype = "pl"
            else:
                levtype = "sfc"

        return levtype

    def _ll_field(self, values_shape, metadata):
        Nj, Ni = values_shape
        metadata["Nj"] = Nj
        metadata["Ni"] = Ni

        # We assume the scanning mode north->south, west->east
        west_east = 360 / Ni

        if Nj % 2 == 0:
            north_south = 180 / Nj
            adjust = north_south / 2
        else:
            north_south = 181 / Nj
            adjust = 0

        north = 90 - adjust
        south = -90 + adjust
        west = 0
        east = 360 - west_east

        metadata["iDirectionIncrementInDegrees"] = west_east
        metadata["jDirectionIncrementInDegrees"] = north_south

        metadata["latitudeOfFirstGridPointInDegrees"] = north
        metadata["latitudeOfLastGridPointInDegrees"] = south
        metadata["longitudeOfFirstGridPointInDegrees"] = west
        metadata["longitudeOfLastGridPointInDegrees"] = east

        edition = metadata.get("edition", 2)
        levtype = self._levtype_from_metadata(metadata)

        return f"regular_ll_{levtype}_grib{edition}"

    def _gg_field(self, values_shape, metadata):
        GAUSSIAN = {
            6114: (32, False),
            13280: (48, False),
            24572: (64, False),
            35718: (80, False),
            40320: (96, True),
            50662: (96, False),
            88838: (128, False),
            108160: (160, True),
            138346: (160, False),
            213988: (200, False),
            348528: (256, False),
            542080: (320, False),
            843490: (400, False),
            1373624: (512, False),
            2140702: (640, False),
            5447118: (1024, False),
            6599680: (1280, True),
            8505906: (1280, False),
            20696844: (2000, False),
        }

        n = values_shape[0]
        if n not in GAUSSIAN:
            raise ValueError(f"Unsupported GAUSSIAN grid. Number of grid points {n:,}")
        N, octahedral = GAUSSIAN[n]

        if N not in self._bbox:
            import eccodes

            self._bbox[N] = max(eccodes.codes_get_gaussian_latitudes(N))

        metadata["latitudeOfFirstGridPointInDegrees"] = self._bbox[N]
        metadata["latitudeOfLastGridPointInDegrees"] = -self._bbox[N]
        metadata["longitudeOfFirstGridPointInDegrees"] = 0

        metadata["N"] = N
        if octahedral:
            half = list(range(20, 20 + N * 4, 4))
            pl = half + list(reversed(half))
            assert len(pl) == 2 * N, (len(pl), 2 * N)
            metadata["pl"] = pl
            metadata["longitudeOfLastGridPointInDegrees"] = 360 - max(pl) / 360
            metadata["Nj"] = len(pl)
        else:
            # We just want the PL
            metadata.update(_gg_pl(N))

        edition = metadata.get("edition", 2)
        levtype = self._levtype_from_metadata(metadata)

        if octahedral or levtype == "sfc":
            return f"reduced_gg_{levtype}_grib{edition}"
        else:
            return f"reduced_gg_{levtype}_{N}_grib{edition}"


def handle_from_metadata(values_shape, metadata, compulsory):

    builder = MetadataHandleBuilder()
    return builder.handle_from_metadata(values_shape, metadata, compulsory)
