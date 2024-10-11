# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
from itertools import product

from earthkit.data.utils.dates import date_to_grib
from earthkit.data.utils.dates import datetime_to_grib
from earthkit.data.utils.dates import step_to_grib
from earthkit.data.utils.dates import time_to_grib
from earthkit.data.utils.dates import to_datetime

LOG = logging.getLogger(__name__)


def update_metadata(metadata, compulsory):
    if "valid_time" in metadata:
        dt = to_datetime(metadata.pop("valid_time"))
        metadata["date"] = dt.date()
        metadata["time"] = dt.time()

    if "forecast_reference_time" in metadata:
        date, time = datetime_to_grib(to_datetime(metadata["forecast_reference_time"]))
        metadata.pop("forecast_reference_time")
        metadata["date"] = date
        metadata["time"] = time

    if "time" in metadata:
        metadata["time"] = time_to_grib(metadata["time"])

    if "date" in metadata:
        date = metadata["date"]
        metadata["date"] = date_to_grib(date)
        if "time" not in metadata:
            if isinstance(date, datetime.datetime):
                metadata["time"] = date.hour * 100 + date.minute

    if "step" in metadata:
        metadata["step"] = step_to_grib(metadata["step"])

    if "stream" not in metadata:
        if "number" in metadata:
            metadata["stream"] = "enfo"
            metadata.setdefault("type", "pf")

    if "levelist" in metadata:
        metadata.setdefault("levtype", "pl")

    if "param" in metadata:
        param = metadata.pop("param")
        try:
            metadata["paramId"] = int(param)
        except ValueError:
            metadata["shortName"] = param

    # levtype is a readOnly key in ecCodes >= 2.33.0
    levtype_remap = {
        "pl": "isobaricInhPa",
        "ml": "hybrid",
        "pt": "theta",
        "pv": "potentialVorticity",
        "sfc": "surface",
    }
    if "levtype" in metadata:
        v = metadata.pop("levtype")
        metadata["typeOfLevel"] = levtype_remap[v]


def coord_to_component(coord):
    if "_earthkit" in coord.attrs:
        keys = coord.attrs["_earthkit"].get("keys", [])
        values = coord.attrs["_earthkit"].get("values", [])

        # for datetime composite coords only the keys are added as an attribute
        if not values and len(coord) == 2:
            values = [datetime_to_grib(to_datetime(x)) for x in coord.values]

        if len(coord) == len(values):
            r = [[a, *b] for a, b in zip(coord.values, values)]
            return r, keys
        else:
            raise ValueError(f"Cannot extract components for coordinate {coord.name}")
    return None


def data_array_to_fields(da, metadata=None):
    from earthkit.data.sources.array_list import ArrayField

    dims = [dim for dim in da.dims if dim not in ["values", "X", "Y", "lat", "lon", "latitude", "longitude"]]
    coords = {k: v for k, v in da.coords.items() if k in dims}
    components = {}
    for k in coords:
        c = coord_to_component(coords[k])
        if c:
            coords[k] = c[0]
            components[k] = c[1]
        else:
            coords[k] = coords[k].values

    # print(f"{coords=}")

    for values in product(*[coords[dim] for dim in dims]):

        # field
        local_coords = dict(zip(dims, values))
        for k in components:
            local_coords[k] = local_coords[k][0]

        # print("local_coords", local_coords)
        xa_field = da.sel(**local_coords)

        # metadata
        grib_metadata = dict(zip(dims, values))
        for k in components:
            # print(f"{k=}")
            # print(grib_metadata[k])
            grib_metadata.update(dict(zip(components[k], grib_metadata[k][1:])))
            # print(f"-> {grib_metadata=}")
            del grib_metadata[k]
        update_metadata(grib_metadata, [])

        # extract metadata from object
        if metadata is None:
            if hasattr(da, "earthkit"):
                metadata = da.earthkit.metadata
            else:
                raise ValueError(
                    "Earthkit attribute not found in DataArray. Required for conversion to FieldList!"
                )

        metadata = metadata.override(grib_metadata)
        yield ArrayField(xa_field.values, metadata)
