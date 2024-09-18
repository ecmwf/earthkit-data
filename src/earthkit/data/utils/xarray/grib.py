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

from earthkit.data.utils.dates import datetime_to_grib
from earthkit.data.utils.dates import to_datetime

LOG = logging.getLogger(__name__)


def update_metadata(self, metadata, compulsory):
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

    if "time" in metadata:  # TODO, use a normalizer
        try:
            time = int(metadata["time"])
            if time < 100:
                metadata["time"] = time * 100
        except ValueError:
            pass

    if "time" not in metadata and "date" in metadata:
        date = metadata["date"]
        metadata["time"] = date.hour * 100 + date.minute

    if "date" in metadata:
        if isinstance(metadata["date"], datetime.datetime):
            date = metadata["date"]
            metadata["date"] = date.year * 10000 + date.month * 100 + date.day
        else:
            metadata["date"] = int(metadata["date"])

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
