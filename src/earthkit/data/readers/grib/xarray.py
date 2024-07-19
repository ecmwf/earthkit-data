# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.utils import ensure_dict
from earthkit.data.utils.kwargs import Kwargs
from earthkit.data.utils.serialise import deserialise_state
from earthkit.data.utils.serialise import serialise_state

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
        return self.item.metadata(n)


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


class XarrayMixIn:

    @staticmethod
    def _kwargs_for_xarray():
        import inspect

        import xarray as xr

        r = inspect.signature(xr.open_dataset)
        v = []
        for p in r.parameters.values():
            if p.kind == p.KEYWORD_ONLY and p.name != "engine":
                v.append(p.name)
        return v

    def xarray_open_dataset_kwargs(self):
        return dict(
            cache=True,  # Set to false to prevent loading the whole dataset
            chunks=None,  # Set to 'auto' for lazy loading
        )

    def to_xarray(self, engine="earthkit", xarray_open_dataset_kwargs=None, **kwargs):
        """
        Convert the FieldList into an xarray DataSet.

        Parameters
        ----------
        engine, str, optional
            The xarray engine to use for generating the dataset. Default value is ``earthkit``.
            If set to ``cfgrib``, the :xref:`cfgrib` engine is used. No other values are
            supported.
        xarray_open_dataset_kwargs: dict, optional
            Keyword arguments passed to ``xarray.open_dataset()``.  Either this or ``**kwargs`` can
            be used, but not both.
        **kwargs: dict, optional
            Other keyword arguments: any keyword arguments that can be passed to
            ``xarray.open_dataset()``. Engine specific keywords are automatically grouped and
            passed as ``backend_kwargs``.  Either ``**kwargs``
            or ``xarray_open_dataset_kwargs`` can be used, but not both.

        The default keyword arguments are as follows::

        - when ``engine`` is "earthkit":

            {"backend_kwargs"= {"errors": "raise"},
            "cache": True, "chunks": None, "engine": "earthkit"}

        - when ``engine`` is "cfgrib":

            {"backend_kwargs": {"errors": "raise", "ignore_keys": [], "squeeze": False,},
            "cache": True, "chunks": None, "engine": "cfgrib"}

        Please note that:

        - ``ignore_keys``  is not supported by :xref:`cfgrib`, but implemented in
            earthkit-data. It specifies the metadata keys that should be ignored when reading
            the GRIB messages in the backend.
        - settings ``errors="raise"`` and ``engine`` are always enforced and cannot
            be changed.

        Returns
        -------
        xarray DataSet or list of xarray DataSets

        Examples
        --------
        >>> import earthkit.data
        >>> fs = earthkit.data.from_source("file", "test6.grib")
        >>> ds = fs.to_xarray(
        ...     xarray_open_dataset_kwargs={
        ...         "backend_kwargs": {"ignore_keys": ["number"]}
        ...     }
        ... )

        """
        engines = {"earthkit": self.to_xarray_earthkit, "cfgrib": self.to_xarray_cfgrib}
        if engine not in engines:
            raise ValueError(f"Unsupported engine: {engine}. Please use one of {list(engines.keys())}")

        user_xarray_open_dataset_kwargs = ensure_dict(xarray_open_dataset_kwargs)
        if user_xarray_open_dataset_kwargs and kwargs:
            raise ValueError("Cannot specify extra keyword arguments when xarray_open_dataset_kwargs is set.")

        if not user_xarray_open_dataset_kwargs:
            user_xarray_open_dataset_kwargs = dict(**kwargs)

        backend_kwargs = user_xarray_open_dataset_kwargs.pop("backend_kwargs", {})
        xr_kwargs = self._kwargs_for_xarray()
        for key in list(user_xarray_open_dataset_kwargs.keys()):
            if key not in xr_kwargs:
                if key in backend_kwargs:
                    raise ValueError(f"Duplicate keyword argument={key}")
                backend_kwargs[key] = user_xarray_open_dataset_kwargs.pop(key)
        user_xarray_open_dataset_kwargs["backend_kwargs"] = backend_kwargs

        return engines[engine](user_xarray_open_dataset_kwargs)

    def to_xarray_earthkit(self, user_kwargs):
        xarray_open_dataset_kwargs = {}

        for key in ["backend_kwargs"]:
            xarray_open_dataset_kwargs[key] = Kwargs(
                user=user_kwargs.pop(key, {}),
                default={"errors": "raise"},
                forced={},
                logging_owner="xarray_open_dataset_kwargs",
                logging_main_key=key,
            )

        # print(f"{xarray_open_dataset_kwargs=}")

        default = dict()
        default.update(self.xarray_open_dataset_kwargs())

        xarray_open_dataset_kwargs.update(
            Kwargs(
                user=user_kwargs,
                default=default,
                forced={
                    # "errors": "raise",
                    "engine": "earthkit",
                },
                logging_owner="xarray_open_dataset_kwargs",
                warn_non_default=False,
            )
        )

        # print(f"{kwargs=}")
        # print(f"{xarray_open_dataset_kwargs=}")

        from earthkit.data.utils.xarray.engine import from_earthkit

        return from_earthkit(self, **xarray_open_dataset_kwargs)

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
        default.update(self.xarray_open_dataset_kwargs())

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
