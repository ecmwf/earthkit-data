# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import SimpleTarget

LOG = logging.getLogger(__name__)


class ZarrTarget(SimpleTarget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zarr_kwargs = kwargs
        self._ekd_kwargs = kwargs.pop("earthkit_to_xarray_kwargs", {})
        self._xr_kwargs = kwargs.pop("xarray_to_zarr_kwargs", {})
        self._encoder = "zarr"

    def close(self):
        """Close the target and flush the fdb.

        The target will not be able to write anymore.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        pass

    def flush(self):
        """Flush the fdb.

        Raises:
        -------
        ValueError: If the target is already closed.
        """
        pass

    def _write(self, data, **kwargs):
        r = self._encode(data, earthkit_to_xarray_kwargs=self._ekd_kwargs)
        ds = r.to_xarray()
        ds.to_zarr(**self._xr_kwargs)


target = ZarrTarget
