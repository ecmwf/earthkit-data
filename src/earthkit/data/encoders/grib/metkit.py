# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

LOG = logging.getLogger(__name__)

_METKIT_KEYS = (
    "accuracy",
    "param",
    "date",
    "time",
    "step",
    "origin",
    "class",
    "stream",
    "type",
    "expver",
    "levtype",
    "levelist",
    "grid",
    "packing",
    # "bitsPerValue",
    "area",
    "hdate",
    # "generatingProcessIdentifier",
)


def is_metkit_key(key):
    return key in _METKIT_KEYS


def _normalise_metadata(metadata):
    if "date" in metadata:
        if isinstance(metadata["date"], datetime.datetime):
            metadata["date"] = metadata["date"].strftime("%Y%m%d")
    return metadata


def handle_from_metkit(values=None, metadata=None):
    assert values is not None, "Values must not be None"
    assert "edition" not in metadata, "Metadata must contain 'edition'"

    import numpy as np
    from pymetkit.experimental.mars2grib import Mars2Grib

    from earthkit.data.readers.grib.handle import GribCodesHandle

    values = np.asarray(values)
    values = values.flatten()

    metadata = _normalise_metadata(metadata)

    encoder = Mars2Grib()
    message = encoder.encode(values, metadata)
    handle = GribCodesHandle.from_message(message)
    return handle
