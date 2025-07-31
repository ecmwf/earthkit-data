# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import xarray
from xarray.backends import BackendEntrypoint

LOG = logging.getLogger(__name__)


class EarthkitBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        source_type="file",
        profile="mars",
        variable_key=None,
        drop_variables=None,
        rename_variables=None,
        mono_variable=None,
        extra_dims=None,
        drop_dims=None,
        ensure_dims=None,
        fixed_dims=None,
        dim_roles=None,
        dim_name_from_role_name=None,
        rename_dims=None,
        dims_as_attrs=None,
        time_dim_mode=None,
        level_dim_mode=None,
        squeeze=None,
        add_valid_time_coord=None,
        decode_times=None,
        decode_timedelta=None,
        add_geo_coords=None,
        attrs_mode=None,
        attrs=None,
        variable_attrs=None,
        global_attrs=None,
        coord_attrs=None,
        add_earthkit_attrs=None,
        rename_attrs=None,
        fill_metadata=None,
        remapping=None,
        flatten_values=None,
        lazy_load=None,
        release_source=None,
        strict=None,
        dtype=None,
        array_module=None,
        array_backend=None,
        errors=None,
    ):
        r"""
        filename_or_obj, str, Path or earthkit object
            Input GRIB file or object to be converted to an xarray dataset.
        profile: str, dict or None
            Provide custom default values for most of the kwargs. Currently, the "mars" and "grid" built-in
            profiles are available, otherwise an explicit dict can
            be used. None is equivalent to an empty dict. When a kwarg is specified it will update
            a default value if it is a dict otherwise it will overwrite it. See: :ref:`xr_profile` for more
            information.
        variable_key: str, None
            Metadata key to specify the dataset variables. It cannot be
            defined as a dimension. Default is "param" (in earthkit-data this is the same as "shortName").
            Only enabled when ``mono_variable`` is False or None.
        drop_variables: str, or iterable of str, None
            A variable or list of variables to drop from the dataset. Default is None. Only used when
            ``variable_key`` is enabled.
        rename_variables: dict, None
            Mapping to rename variables. Default is None. Only used  when
            ``variable_key`` is enabled.
        mono_variable: bool, str, None
            If True or str, the dataset will contain a single variable called "data" (or the value
            of the ``mono_variable`` kwarg when it is a str). If False, the dataset will contain
            one variable for each distinct value of ``variable_key`` metadata key. The default value
            (None) expands to False unless the ``profile`` overwrites it.
        extra_dims:  str, or iterable of str, None
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

        drop_dims:  str, or iterable of str, None
            Single or multiple dimensions to be ignored. Default is None.
            Default is None.
        ensure_dims: str, or iterable of str, None
            Dimension or dimensions that should be kept even when ``squeeze=True`` and their size
            is only 1. Default is None.
        fixed_dims: str, or iterable of str, None
            Define all the dimensions to be generated. When used no other dimensions will be created.
            Might be incompatible with other settings. Default is None. It can be a single item or a list.
            Each item is either a metadata key, or a dict/tuple defining mapping between the dimension
            name and the metadata key. The whole option can be a dict. E.g.

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

        dim_roles: dict, None
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
        dim_name_from_role_name: bool, None
            If True, the dimension names are formed from the role names. Otherwise the
            dimension names are formed from the metadata keys specified in ``dim_roles``.
            Its default value (None) expands to True unless the ``profile`` overwrites it.
            Only used when no `fixed_dims`` are specified. *New in version 0.15.0*.
        rename_dims: dict, None
            Mapping to rename dimensions. Default is None.
        dims_as_attrs: str, or iterable of str, None
            Dimension or list of dimensions which should be turned to variable
            attributes if they have only one value for the given variable. Default is None.
        time_dim_mode: str, None
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
        level_dim_mode: str, None
            Define how predefined vertical dimensions are formed. The default is "level".
            The possible values are:

            - "level": adds a single dimension according to the "level" role (see ``dim_roles``)
            - "level_per_type": adds a separate dimensions for each level type based on the
              "level" and "level_type" roles.
            - "level_and_type": Use a single dimension for combined level and type of level.
        squeeze: bool, None
            Remove dimensions which have only one valid value. Not applies to dimensions in
            ``ensure_dims``. Its default value (None) expands
            to True unless the ``profile`` overwrites it.
        add_valid_time_coord: bool, None
            Add the `valid_time` coordinate containing np.datetime64 values to the
            dataset. Only makes effect when ``time_dim_mode`` is not "valid_time". Its default
            value (None) expands to False unless the ``profile`` overwrites it.
        decode_times: bool, None
            If True, decode date and datetime coordinates into datetime64 values. If False, leave
            coordinates representing date-like GRIB keys (e.g. "date", "validityDate") encoded as
            native int values. The default value (None) expands to True unless the ``profile``
            overwrites it.
        decode_timedelta: bool, None
            If True, decode coordinates representing time-like or duration-like GRIB keys
            (e.g. "time", "validityTime", "step") into timedelta64 values. If False, leave time-like
            coordinates encoded as native int values, while duration-like coordinates will be encoded
            as int with the units attached to the coordinate as the "units" attribute.
            If None (default), assume the same value of ``decode_times`` unless the ``profile``
            overwrites it.
        add_geo_coords: bool, None
            If True, add geographic coordinates to the dataset when field values are represented by
            a single "values" dimension. Its default value (None) expands
            to True unless the ``profile`` overwrites it.
        flatten_values: bool, None
            if True, flatten the values per field resulting in a single dimension called
            "values" representing a field. Otherwise the field shape is used to form
            the field dimensions. When the fields are defined on an unstructured grid (e.g.
            reduced Gaussian) or are spectral (e.g. spherical harmonics) this option is
            ignored and the field values are always represented by a single "values"
            dimension.  Its default value (None) expands
            to False unless the ``profile`` overwrites it.
        attrs_mode: str, None
            Define how attributes are generated. Default is "fixed". The possible values are:

            - "fixed": Use the attributes defined in ``variable_attrs`` as variables
              attributes and ``global_attrs`` as global attributes.
            - "unique": Use all the attributes defined in ``attrs``, ``variable_attrs``
              and ``global_attrs``. When an attribute has unique value for a dataset
              it will be a global attribute, otherwise it will be a variable attribute.
              However, this logic is only applied if a unique variable attribute can be
              a global attribute according to the CF conventions Appendix A. (e.g. "units" cannot
              be a global attribute). Additionally, keys in ``variable_attrs`` are always used as
              variable attributes, while keys in ``global_attrs`` are always used as global attributes.
        attrs: str, number, callable, dict or list of these, None
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
        variable_attrs: str, number, callable, dict or list of these, None
            Variable attribute or attributes. For the allowed values see ``attrs``. Its
            default value (None) expands to [] unless the ``profile`` overwrites it.
        global_attrs: str, number, dict or list of these, None
            Global attribute or attributes. For the allowed values see ``attrs``. Its
            default value (None) expands to [] unless the ``profile`` overwrites it.
        coord_attrs: dict, None
            To be documented. Default is None.
        add_earthkit_attrs: bool, None
            If True, add earthkit specific attributes to the dataset. Its default value
            (None) expands to True unless the ``profile`` overwrites it.
        rename_attrs: dict, None
            A dictionary of attribute to rename. Default is None.
        fill_metadata: dict, None
            Define fill values to metadata keys. Default is None.
        remapping: dict, None
            Define new metadata keys for indexing. Default is None.
        lazy_load: bool, None
            If True, the resulting Dataset will load data lazily from the
            underlying data source. If False, a DataSet holding all the data in memory
            and decoupled from the backend source will be created.
            Using ``lazy_load=False`` with ``release_source=True`` can provide optimised
            memory usage in certain cases. The default value of ``lazy_load`` (None)
            expands to True unless the ``profile`` overwrites it.
        release_source: bool, None
            Only used when ``lazy_load=False``. If True, memory held in the input fields are
            released as soon as their values are copied into the resulting Dataset. This is
            done per field to avoid memory spikes. The release operation is currently
            only supported for GRIB fields stored entirely in memory, e.g. when read from a
            :ref:`stream <streams>`. When a field does not support the release operation, this
            option is ignored. Having run :obj:`to_xarray` the input data becomes unusable,
            so use this option carefully. The default value of ``release_source`` (None) expands
            to False unless the ``profile`` overwrites it.
        strict: bool, None
            If True, perform stricter checks on hypercube consistency. Its default value (None) expands
            to False unless the ``profile`` overwrites it.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array data.
        array_backend: str, array namespace, ArrayBackend, None
            The array backend/namespace to use for array operations. The default value (None) is
            expanded to "numpy".
        """
        fieldlist = self._fieldlist(filename_or_obj, source_type)

        if hasattr(fieldlist, "_ek_builder"):
            builder = fieldlist._ek_builder
            return builder.build()
        else:
            from .builder import SingleDatasetBuilder

            if array_module is not None:
                import warnings

                warnings.warn("'array_module' is deprecated. Use 'array_backend' instead", DeprecationWarning)
                if array_backend is None:
                    array_backend = array_module

            _kwargs = dict(
                variable_key=variable_key,
                drop_variables=drop_variables,
                rename_variables=rename_variables,
                mono_variable=mono_variable,
                extra_dims=extra_dims,
                drop_dims=drop_dims,
                ensure_dims=ensure_dims,
                fixed_dims=fixed_dims,
                rename_dims=rename_dims,
                dim_roles=dim_roles,
                dim_name_from_role_name=dim_name_from_role_name,
                dims_as_attrs=dims_as_attrs,
                time_dim_mode=time_dim_mode,
                level_dim_mode=level_dim_mode,
                squeeze=squeeze,
                attrs_mode=attrs_mode,
                attrs=attrs,
                variable_attrs=variable_attrs,
                global_attrs=global_attrs,
                coord_attrs=coord_attrs,
                add_earthkit_attrs=add_earthkit_attrs,
                rename_attrs=rename_attrs,
                add_valid_time_coord=add_valid_time_coord,
                add_geo_coords=add_geo_coords,
                flatten_values=flatten_values,
                fill_metadata=fill_metadata,
                remapping=remapping,
                decode_times=decode_times,
                decode_timedelta=decode_timedelta,
                lazy_load=lazy_load,
                release_source=release_source,
                strict=strict,
                dtype=dtype,
                array_backend=array_backend,
                errors=errors,
            )

            return SingleDatasetBuilder(fieldlist, profile, from_xr=True, backend_kwargs=_kwargs).build()

    @classmethod
    def guess_can_open(cls, filename_or_obj):
        try:
            from earthkit.data.core import Base

            if isinstance(filename_or_obj, Base):
                return True
            elif isinstance(filename_or_obj, str):
                from earthkit.data.readers.grib import is_grib_file

                return is_grib_file(filename_or_obj)
        except Exception:
            LOG.debug(
                "Failed to guess if %s can be opened by the earthkit backend", filename_or_obj, exc_info=True
            )

        return False

    @staticmethod
    def _fieldlist(filename_or_obj, source_type):
        import os
        import pathlib

        from earthkit.data.core import Base

        if isinstance(filename_or_obj, Base):
            ds = filename_or_obj
        elif isinstance(filename_or_obj, (str, os.PathLike, pathlib.Path)):
            from earthkit.data import from_source

            ds = from_source(source_type, filename_or_obj)
        return ds


class XarrayEarthkit:
    def to_fieldlist(self):
        from earthkit.data.indexing.fieldlist import FieldArray

        return FieldArray([f for f in self._to_fields()])

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self._obj, **kwargs)

    def to_grib(self, filename):
        import warnings

        warnings.warn(
            "The `to_grib` is deprecated in 0.15.0 and will be removed in a future version. "
            "Use `to_target` instead.",
            DeprecationWarning,
        )
        from earthkit.data.targets import create_target

        with create_target("file", filename) as target:
            for f in self._to_fields():
                target.write(f)

    def _generator(self):
        from earthkit.data import FieldList

        class GeneratorFieldList(FieldList):
            def __init__(self, data):
                self._data = data

            def mutate(self):
                return self

            def __iter__(self):
                return self._data

            def default_encoder(self):
                return "grib"

        return GeneratorFieldList(self._to_fields())


@xarray.register_dataarray_accessor("earthkit")
class XarrayEarthkitDataArray(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    @property
    def metadata(self):
        md = self._obj.attrs.get("_earthkit", dict())
        if "message" in md:
            data = md["message"]
            from earthkit.data.readers.grib.memory import GribMessageMemoryReader
            from earthkit.data.readers.grib.metadata import StandAloneGribMetadata
            from earthkit.data.readers.grib.metadata import WrappedMetadata

            handle = next(GribMessageMemoryReader(data)).handle
            bpv = md.get("bitsPerValue", 0)
            res_md = StandAloneGribMetadata(handle)
            if bpv is not None and bpv > 0:
                return WrappedMetadata(res_md, extra={"bitsPerValue": bpv})
            else:
                return res_md

        raise ValueError(
            (
                "Could not generate earthkit metadata from xarray object."
                "Attribute '_earthkit' is missing or contains incorrect data."
            )
        )

    def _remove_earthkit_attrs(self):
        """Create a copy of the dataarray and remove earthkit attributes."""
        da = self._obj
        if "_earthkit" in da.attrs:
            da = da.copy()
            del da.attrs["_earthkit"]
        return da

    def _to_fields(self):
        from .grib import data_array_to_fields

        for f in data_array_to_fields(self._obj, metadata=self.metadata):
            yield f

    def to_netcdf(self, *args, **kwargs):
        """Remove earthkit attributes before writing to netcdf."""
        ds = self._obj
        if "_earthkit" in self._obj.attrs:
            ds = self._remove_earthkit_attrs()

        return ds.to_netcdf(*args, **kwargs)

    def to_device(self, device, *args, array_backend=None, **kwargs):
        """Return a **new** DataArray whose data live on *device*."""
        from earthkit.utils.array import to_device

        moved = to_device(self._obj.data, device, *args, array_backend=array_backend, **kwargs)
        da = self._obj.copy(deep=False)
        da.data = moved
        return da

    @property
    def grid_spec(self):
        """Return the grid specification of the DataArray."""
        try:
            return self.metadata.gridspec
        except Exception:
            return None


@xarray.register_dataset_accessor("earthkit")
class XarrayEarthkitDataSet(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def _to_fields(self):
        from .grib import data_array_to_fields

        for var in self._obj.data_vars:
            for f in data_array_to_fields(self._obj[var]):
                yield f

    def _remove_earthkit_attrs(self):
        """Create a copy of the dataset and remove earthkit attributes."""
        ds = self._obj.copy()
        for var in ds.data_vars:
            if "_earthkit" in ds[var].attrs:
                del ds[var].attrs["_earthkit"]

        return ds

    def to_netcdf(self, *args, **kwargs):
        """Remove earthkit attributes before writing to netcdf."""
        ds = self._obj
        for var in self._obj.data_vars:
            if "_earthkit" in self._obj[var].attrs:
                ds = self._remove_earthkit_attrs()
                break

        return ds.to_netcdf(*args, **kwargs)

    def to_device(self, device, *args, array_backend=None, **kwargs):
        """Return a new Dataset with every data variable on the specified ``device``."""
        from earthkit.utils.array import to_device

        ds = self._obj.copy(deep=False)
        for name, var in ds.data_vars.items():
            ds[name].data = to_device(var.data, device, *args, array_backend=array_backend, **kwargs)
        return ds

    @property
    def grid_spec(self):
        """Return the grid specification of the DataSet."""
        try:
            # return grid spec of the first data variable
            var = list(self._obj.data_vars.values())[0]
            return var.earthkit.grid_spec

        except Exception:
            return None
