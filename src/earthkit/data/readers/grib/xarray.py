# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.utils.kwargs import Kwargs
from earthkit.data.utils.serialise import deserialise_state, serialise_state

LOG = logging.getLogger(__name__)


class ItemWrapperForCfGrib:
    def __init__(self, item, ignore_keys=[]):
        self.item = item
        self.ignore_keys = ignore_keys

    def __getitem__(self, n):
        if n in self.ignore_keys:
            return None
        if n == "values":
            return self.item.values
        return self.item.get(f"metadata.{n}", raise_on_missing=True)


class IndexWrapperForCfGrib:
    def __init__(self, index=None, ignore_keys=[]):
        self.index = index
        self.ignore_keys = ignore_keys

    def __getstate__(self):
        return dict(index=serialise_state(self.index), ignore_keys=self.ignore_keys)

    def __setstate__(self, state):
        self.index = deserialise_state(state["index"])
        self.ignore_keys = state["ignore_keys"]

    def __getitem__(self, n):
        return ItemWrapperForCfGrib(
            self.index[n],
            ignore_keys=self.ignore_keys,
        )

    def __len__(self):
        return len(self.index)


def to_xarray_cfgrib(self, user_kwargs):
    xarray_open_dataset_kwargs = {}

    # until ignore_keys is included into cfgrib,
    # it is implemented here directly
    ignore_keys = user_kwargs.get("backend_kwargs", {}).pop("ignore_keys", [])

    for key in ["backend_kwargs"]:
        xarray_open_dataset_kwargs[key] = Kwargs(
            user=user_kwargs.pop(key, {}),
            default={"errors": "raise", "squeeze": False},
            forced={},
            logging_owner="xarray_open_dataset_kwargs",
            logging_main_key=key,
        )

    # default = dict(squeeze=False)  # TODO:Document me
    default = dict()
    default.update(self._xarray_open_dataset_kwargs())

    xarray_open_dataset_kwargs.update(
        Kwargs(
            user=user_kwargs,
            default=default,
            forced={
                # "errors": "raise",
                "engine": "cfgrib",
            },
            logging_owner="xarray_open_dataset_kwargs",
            warn_non_default=False,
        )
    )

    open_object = IndexWrapperForCfGrib(self, ignore_keys=ignore_keys)

    import xarray as xr

    return xr.open_dataset(
        open_object,
        # decode_cf=False,
        **xarray_open_dataset_kwargs,
    )
