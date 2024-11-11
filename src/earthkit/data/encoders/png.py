# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import Encoder

LOG = logging.getLogger(__name__)


class PngPresenter:
    def __init__(self, data):
        self.data = data

    def to_bytes(self, data):
        return data

    def to_file(self, f):
        import imageio

        imageio.imwrite(f, self.data)

    def write(self, f):
        import imageio

        imageio.imwrite(f, self.data, format="png")


class PngEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        values=None,
        min=None,
        max=None,
        check_nans=False,
        metadata={},
        template=None,
        # return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        from earthkit.data.wrappers import get_wrapper

        if values is None:
            if data is not None:
                data = get_wrapper(data)
                values = data.to_numpy()
            else:
                raise ValueError("No values to encode")

        if values.ndim != 2:
            raise ValueError("PNG encoder only supports 2D arrays")

        import numpy as np

        if min is None:
            min = values.min()
        if max is not None:
            ptp = values.max() - min
        else:
            ptp = np.ptp(values)

        d = (255 * (values - min) / ptp).astype(np.uint8)
        return PngPresenter(d)


Encoder = PngEncoder
