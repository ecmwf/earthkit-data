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
    # # TODO: revisit that logic
    # combined = Combined(handle, metadata)

    # if "step" in metadata or "endStep" in metadata:
    #     if combined["type"] == "an":
    #         metadata["type"] = "fc"

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

    # if "number" in metadata:
    #     compulsory += ("numberOfForecastsInEnsemble",)
    #     productDefinitionTemplateNumber = {"tp": 11}
    #     metadata["productDefinitionTemplateNumber"] = productDefinitionTemplateNumber.get(
    #         handle.get("shortName"), 1
    #     )

    # if metadata.get("type") in ("pf", "cf"):
    #     metadata.setdefault("typeOfGeneratingProcess", 4)

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


def data_array_to_fields(da):
    from earthkit.data.sources.array_list import ArrayField

    dims = [dim for dim in da.dims if dim not in ["values", "X", "Y", "lat", "lon", "latitude", "longitude"]]
    coords = {key: value for key, value in da.coords.items() if key in dims}
    # for k, v in coords.items():
    #     print(k, v.name, v.values)

    for values in product(*[coords[dim].values for dim in dims]):
        local_coords = dict(zip(dims, values))
        grib_metadata = dict(**local_coords)
        update_metadata(grib_metadata, [])

        xa_field = da.sel(**local_coords)

        # extract metadata from object
        if hasattr(da, "earthkit"):
            metadata = da.earthkit.metadata
        else:
            raise ValueError(
                "Earthkit attribute not found in DataArray. Required for conversion to FieldList!"
            )

        metadata = metadata.override(grib_metadata)
        yield ArrayField(xa_field.values, metadata)
