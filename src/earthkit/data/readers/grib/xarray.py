# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import copy
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
        Convert the FieldList into an Xarray Dataset.

        Parameters
        ----------
        engine: str, optional
            The Xarray engine to use for generating the dataset. Default value is ``"earthkit"``.
            If set to ``cfgrib``, the :xref:`cfgrib` engine is used. No other values are
            supported.
        split_dims: str, or iterable of str, None
            Dimension or list of dimensions to use for splitting the data into multiple hypercubes.
            Default is None. Only used when ``engine="earthkit"``. Please note that ``split_dims``
            is not a valid option when the Xarray is directly generated via
            :py:meth:`xarray.open_dataset`.
        xarray_open_dataset_kwargs: dict, optional
            Keyword arguments passed to :py:func:`xarray.open_dataset`. Either this or ``**kwargs`` can
            be used, but not both.
        **kwargs: dict, optional
            Any keyword arguments that can be passed to :py:func:`xarray.open_dataset`. Engine specific
            keywords are automatically grouped and passed as ``backend_kwargs``.  Either ``**kwargs``
            or ``xarray_open_dataset_kwargs`` can be used, but not both.

            When ``engine="earthkit"`` the following engine specific kwargs are supported:

            * profile: str, dict or None
                Provide custom default values for most of the kwargs. Currently, the "mars" and "grid"
                built-in profiles are available, otherwise an explicit dict can be used. None is equivalent
                to an empty dict. When a kwarg is specified it will update
                a default value if it is a dict otherwise it will overwrite it. See: :ref:`xr_profile` for
                more information.
            * variable_key: str, None
                Metadata key to specify the dataset variables. It cannot be
                defined as a dimension. Default is "param" (in earthkit-data this is the same as "shortName").
                Only enabled when ``mono_variable`` is False or None.
            * drop_variables: str, or iterable of str, None
                A variable or list of variables to drop from the dataset. Default is None. Only used when
                ``variable_key`` is enabled.
            * rename_variables: dict, None
                Mapping to rename variables. Default is None. Only used  when
                ``variable_key`` is enabled.
            * mono_variable: bool, str, None
                If True or str, the dataset will contain a single variable called "data" (or the value
                of the ``mono_variable`` kwarg when it is a str). If False, the dataset will contain
                one variable for each distinct value of ``variable_key`` metadata key. The default value
                (None) expands to False unless the ``profile`` overwrites it.
            * extra_dims:  str, or iterable of str, None
                Define additional dimensions on top of the predefined dimensions. Only enabled when no
                ``fixed_dims`` is specified. Default is None. It can be a single item or a list. Each
                item is either a metadata key, or a dict/tuple defining mapping between the dimension
                name and the metadata key. The whole option can be a dict. E.g.

                .. code-block:: python

                    # use key "expver" as a dimension
                    extra_dims = "expver"
                    # use keys "expver" and "steam" as a dimension
                    extra_dims = ["expver", "stream"]
                    # define dimensions "expver", mars_stream" and "mars_type" from
                    # metadata keys "expver", "stream" and "type"
                    extra_dims = [
                        "expver",
                        {"mars_stream": "stream"},
                        ("mars_type", "type"),
                    ]
                    extra_dims = [
                        {
                            "expver": "expver",
                            "mars_stream": "stream",
                            "mars_type": "type",
                        }
                    ]

            * drop_dims:  str, or iterable of str, None
                Single or multiple dimensions to be ignored. Default is None.
                Default is None.
            * ensure_dims: str, or iterable of str, None
                Dimension or dimensions that should be kept even when ``squeeze=True`` and their size
                is only 1. Default is None.
            * fixed_dims: str, or iterable of str, None
                Define all the dimensions to be generated. When used no other dimensions will be created.
                Might be incompatible with other settings. Default is None. It can be a single item or a list.
                Each item is either a metadata key, or a dict/tuple defining mapping between the dimension
                name and the metadata key. The whole option can be a dict. E.g.:

                .. code-block:: python

                    # use key "step" as a dimension
                    fixed_dims = "step"
                    # use keys "step" and "levelist" as a dimension
                    extra_dims = ["step", "levelist"]
                    # define dimensions "step", level" and "level_type" from
                    # metadata keys "step", "levelist" and "levtype"
                    extra_dims = [
                        "step",
                        {"level": "levelist"},
                        ("level_type", "levtype"),
                    ]
                    extra_dims = [
                        {"step": "step", "level": "levelist", "level_type": "levtype"}
                    ]

            * dim_roles: dict, None
                Specify the "roles" used to form the predefined dimensions. The predefined dimensions are
                automatically generated when no ``fixed_dims`` specified and comprise the following
                (in a fixed order):

                - ensemble forecast member dimension
                - temporal dimensions (controlled by ``time_dim_mode``)
                - vertical dimensions (controlled by ``level_dim_mode``)

                ``dim_roles`` is a mapping between the "roles" and the metadata keys representing the roles.
                The possible roles are as follows:

                - "number": metadata key interpreted as ensemble forecast members
                - "date": metadata key interpreted as date part of the "forecast_reference_time"
                - "time": metadata key interpreted as time part of the "forecast_reference_time"
                - "step": metadata key interpreted as forecast step
                - "forecast_reference_time": if not specified or None or empty the forecast reference
                  time is built using the "date" and "time" roles
                - "valid_time": if not specified or None or empty the valid time is built using the
                  "validityDate" and "validityTime" metadata keys
                - "level": metadata key interpreted as level
                - "level_type": metadata key interpreted as level type

                The default values are as follows:

                .. code-block:: python

                    {
                        "number": "number",
                        "date": "dataDate",
                        "time": "dataTime",
                        "step": "step",
                        "forecast_reference_time": None,
                        "valid_date": None,
                        "level": "level",
                        "level_type": "typeOfLevel",
                    }

                ``dims_roles`` behaves differently to the other kwargs in the sense that
                it does not override but update the default values. So e.g. to change only "number" in
                the defaults it is enough to specify: "dim_roles={"number": "perturbationNumber"}.
            * dim_name_from_role_name: bool, None
                If True, the dimension names are formed from the role names. Otherwise the
                dimension names are formed from the metadata keys specified in ``dim_roles``.
                Its default value (None) expands to True unless the ``profile`` overwrites it.
                Only used when no `fixed_dims`` are specified. *New in version 0.15.0*.
            * rename_dims: dict, None
                Mapping to rename dimensions. Default is None.
            * dims_as_attrs: str, or iterable of str, None
                Dimension or list of dimensions which should be turned to variable
                attributes if they have only one value for the given variable. Default is None.
            * time_dim_mode: str, None
                Define how predefined temporal dimensions are formed. The default is "forecast".
                The possible values are as follows:

                - "forecast": adds two dimensions:

                  - "forecast_reference_time": built from the "date" and "time" roles
                    (see ``dim_roles``) as np.datetime64 values
                  - "step": built from the "step" role. When ``decode_time=True`` the values are
                    np.timedelta64
                - "valid_time": adds a dimension called "valid_time" as described by the "valid_time"
                  role (see ``dim_roles``). Will contain np.datetime64 values.
                - "raw": the "date", "time" and "step" roles are turned into 3 separate dimensions
            * level_dim_mode: str, None
                Define how predefined vertical dimensions are formed. The default is "level".
                The possible values are:

                - "level": adds a single dimension according to the "level" role (see ``dim_roles``)
                - "level_per_type": adds a separate dimensions for each level type based on the
                  "level" and "level_type" roles.
                - "level_and_type": Use a single dimension for combined level and type of level.
            * squeeze: bool, None
                Remove dimensions which have only one valid value. Not applies to dimensions in
                ``ensure_dims``. Its default value (None) expands
                to True unless the ``profile`` overwrites it.
            * add_valid_time_coord: bool, None
                If True, add the `valid_time` coordinate containing np.datetime64 values to the
                dataset. Only makes effect when ``time_dim_mode`` is not "valid_time". Its default
                value (None) expands to False unless the ``profile`` overwrites it.
            * decode_times: bool, None
                If True, decode date and datetime coordinates into datetime64 values. If False, leave
                coordinates representing date-like GRIB keys (e.g. "date", "validityDate") encoded as
                native int values. The default value (None) expands to True unless the ``profile``
                overwrites it.
            * decode_timedelta: bool, None
                If True, decode coordinates representing time-like or duration-like GRIB keys
                (e.g. "time", "validityTime", "step") into timedelta64 values. If False, leave time-like
                coordinates encoded as native int values, while duration-like coordinates will be encoded
                as int with the units attached to the coordinate as the "units" attribute.
                If None (default), assume the same value of ``decode_times`` unless the ``profile``
                overwrites it.
            * add_geo_coords: bool, None
                Add geographic coordinates to the dataset when field values are represented by
                a single "values" dimension. Its default value (None) expands
                to True unless the ``profile`` overwrites it.
            * flatten_values: bool, None
                If True, flatten the values per field resulting in a single dimension called
                "values" representing a field. If False, the field shape is used to form
                the field dimensions. When the fields are defined on an unstructured grid (e.g.
                reduced Gaussian) or are spectral (e.g. spherical harmonics) this option is
                ignored and the field values are always represented by a single "values"
                dimension.  Its default value (None) expands
                to False unless the ``profile`` overwrites it.
            * attrs_mode: str, None
                Define how attributes are generated. Default is "fixed". The possible values are:

                - "fixed": Use the attributes defined in ``variable_attrs`` as variables
                  attributes and ``global_attrs`` as global attributes.
                - "unique": Use all the attributes defined in ``attrs``, ``variable_attrs``
                  and ``global_attrs``.  When an attribute has unique value for a dataset
                  it will be a global attribute, otherwise it will be a variable attribute.
                  However, this logic is only applied if a unique variable attribute can be
                  a global attribute according to the CF conventions Appendix A. (e.g. "units" cannot
                  be a global attribute). Additionally, keys in ``variable_attrs`` are always used as
                  variable attributes, while keys in ``global_attrs`` are always used as global attributes.
            * attrs: str, number, callable, dict or list of these, None
                Attribute or list of attributes. Only used when ``attrs_mode`` is ``unique``.
                Its default value (None) expands to [] unless the ``profile`` overwrites it.
                The following attributes are supported:

                - str: Name of the attribute used as a metadata key to generate the value of
                  the attribute. Can also be specified by prefixing with "key=" (e.g. "key=level").
                  When prefixed with "namespace=" it specifies a metadata namespace
                  (e.g. "namespace=parameter"), which will be added as a dict to the attribute.
                - callable: A callable that takes a Metadata object and returns a dict of attributes
                - dict: A dictionary of attributes with the keys as the attribute names.
                  If the value is a callable it takes the attribute name and a Metadata object and
                  returns the value of the attribute. A str value prefixed with "key=" or
                  "namespace=" is interpreted as explained above. Any other values are used as the
                  pre-defined value for the attribute.
            * variable_attrs: str, number, callable, dict or list of these, None
                Variable attribute or attributes. For the allowed values see ``attrs``. Its
                default value (None) expands to [] unless the ``profile`` overwrites it.
            * global_attrs: str, number, dict or list of these, None
                Global attribute or attributes. For the allowed values see ``attrs``. Its
                default value (None) expands to [] unless the ``profile`` overwrites it.
            * coord_attrs: dict, None
                To be documented. Default is None.
            * add_earthkit_attrs: bool, None
                If True, add earthkit specific attributes to the dataset. Its default value
                (None) expands to True unless the ``profile`` overwrites it.
            * rename_attrs: dict, None
                A dictionary of attribute to rename. Default is None.
            * fill_metadata: dict, None
                Define fill_metadata values to metadata keys. Default is None.
            * remapping: dict, None
                Define new metadata keys for indexing. Default is None.
            * lazy_load: bool, None
                If True, the resulting Dataset will load data lazily from the
                underlying data source. If False, a Dataset holding all the data in memory
                and decoupled from the backend source will be created.
                Using ``lazy_load=False`` with ``release_source=True`` can provide optimised
                memory usage in certain cases. The default value of ``lazy_load`` (None)
                expands to True unless the ``profile`` overwrites it.
            * release_source: bool, None
                Only used when ``lazy_load=False``. If True, memory held in the input fields are
                released as soon as their values are copied into the resulting Dataset. This is
                done per field to avoid memory spikes. The release operation is currently
                only supported for GRIB fields stored entirely in memory, e.g. when read from a
                :ref:`stream <streams>`. When a field does not support the release operation, this
                option is ignored. Having run :obj:`to_xarray` the input data becomes unusable,
                so use this option carefully. The default value of ``release_source`` (None) expands
                to False unless the ``profile`` overwrites it.
            * strict: bool, None
                If True, perform stricter checks on hypercube consistency. Its default value (None) expands
                to False unless the ``profile`` overwrites it.
            * dtype: str, numpy.dtype or None
                Typecode or data-type of the array data.
            * array_backend: str, array namespace, ArrayBackend, None
                The array backend/namespace to use for array operations. The default value (None) is
                expanded to "numpy".
            * direct_backend: bool, None
                If True, the backend is used directly bypassing :py:meth:`xarray.open_dataset`
                and ignoring all non-backend related kwargs. If False, the data is read via
                :py:meth:`xarray.open_dataset`. Its default value (None) expands
                to False unless the ``profile`` overwrites it.

            When ``engine="cfgrib"`` the following engine specific kwargs are supported:

            * ignore_keys: list, None
                It specifies the metadata keys that should be ignored when reading
                the GRIB messages in the backend. Please note that is not supported by :xref:`cfgrib`, but
                implemented in earthkit-data.
            * For the rest of the supported keyword arguments, please refer to the
              :xref:`cfgrib` documentation.


        Returns
        -------
        Xarray Dataset or tuple
            When ``split_dims`` is unset a Dataset is returned. When ``engine="earthkit"``
            and ``split_dims`` is set a tuple is returned. The first element of the tuple is the list
            of Datasets and the second element is the list of corresponding dictionaries with
            the spitting keys/values (one dictionary per Dataset).

        Notes
        -----
        The default values of ``xarray_open_dataset_kwargs`` or ``**kwargs`` passed
        to :py:func:`xarray.open_dataset` are as follows:

            - when ``engine="earthkit"``::

               {"cache": True, "chunks": None, "engine": "earthkit"}

            - when ``engine="cfgrib"``::

                {"backend_kwargs": {"errors": "raise", "ignore_keys": [], "squeeze": False,},
                "cache": True, "chunks": None, "engine": "cfgrib"}

        Please note that settings ``errors="raise"`` and ``engine`` are always enforced
        and cannot be changed.


        Examples
        --------
        >>> import earthkit.data
        >>> fs = earthkit.data.from_source("file", "test6.grib")
        >>> ds = fs.to_xarray(time_dim_mode="forecast")
        >>> # also possible to use the xarray_open_dataset_kwargs
        >>> ds = fs.to_xarray(
        ...     xarray_open_dataset_kwargs={
        ...         "backend_kwargs": {"time_dim_mode": "forecast"}
        ...     }
        ... )

        """
        engines = {"earthkit": self.to_xarray_earthkit, "cfgrib": self.to_xarray_cfgrib}
        if engine not in engines:
            raise ValueError(f"Unsupported engine: {engine}. Please use one of {list(engines.keys())}")

        user_xarray_open_dataset_kwargs = ensure_dict(xarray_open_dataset_kwargs)
        user_xarray_open_dataset_kwargs = copy.deepcopy(user_xarray_open_dataset_kwargs)
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

        # separate backend_kwargs from other_kwargs
        backend_kwargs = xarray_open_dataset_kwargs.pop("backend_kwargs", None)
        other_kwargs = xarray_open_dataset_kwargs

        from earthkit.data.utils.xarray.builder import from_earthkit

        return from_earthkit(self, backend_kwargs=backend_kwargs, other_kwargs=other_kwargs)

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
