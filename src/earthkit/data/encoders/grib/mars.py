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


def _normalise_metadata(metadata):
    if "date" in metadata:
        if isinstance(metadata["date"], (datetime.datetime, datetime.date)):
            metadata["date"] = metadata["date"].strftime("%Y%m%d")
    return metadata


def handle_from_mars(values=None, metadata=None):
    assert values is not None, "Values must not be None"
    assert "edition" not in metadata, "Metadata must not contain 'edition'"

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
