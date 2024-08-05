# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from itertools import product

import numpy
import xarray
from xarray.backends import BackendEntrypoint

LOG = logging.getLogger(__name__)


def from_earthkit(ds, **kwargs):
    backend_kwargs = kwargs.get("backend_kwargs", {})
    auto_split = backend_kwargs.get("auto_split", False)
    split_dims = backend_kwargs.get("split_dims", None)

    assert kwargs["engine"] == "earthkit"

    if not auto_split and not split_dims:
        backend_kwargs.pop("auto_split", None)
        backend_kwargs.pop("split_dims", None)
        return xarray.open_dataset(ds, **kwargs)
    else:
        from .builder import SplitDatasetBuilder

        backend_kwargs = kwargs.pop("backend_kwargs", {})
        return SplitDatasetBuilder(ds, backend_kwargs=backend_kwargs, **kwargs).build()


class EarthkitBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        source_type="file",
        profile="mars",
        variable_key="param",
        drop_variables=None,
        rename_variables=None,
        extra_dims=None,
        drop_dims=None,
        ensure_dims=None,
        fixed_dims=None,
        dim_roles=None,
        rename_dims=None,
        dims_as_attrs=None,
        time_dim_mode="forecast",
        level_dim_mode="level",
        squeeze=True,
        add_valid_time_coord=True,
        decode_time=True,
        add_geo_coords=True,
        remapping=None,
        flatten_values=False,
        attrs_mode="fixed",
        attrs=["cfName", "name", "units", "typeOfLevel"],
        variable_attrs=None,
        global_attrs=None,
        coord_attrs=None,
        rename_attrs={"cfName": "standard_name", "name": "long_name"},
        strict=True,
        errors=None,
        dtype=None,
        array_module=numpy,
    ):
        r"""
        filename_or_obj, str, Path or earthkit object
            Input GRIB file or object to be converted to an xarray dataset.
        profile: str, dict or None
            Provide custom default values for the kwargs. Two built-in profiles are available by using their
            names: "mars" and "grid". Otherwise an explicit dict can be used. None is equivalent to an empty
            dict. When a kwarg is specified it will override the profile values.
        variable_key: str, None
            Metadata key to specify the dataset variables. It cannot be
            defined as a dimension. Default is "param".
        drop_variables: str, or iterable of str, None
            A variable or list of variables to drop from the dataset. Default is None.
        rename_variables: dict, None
            Mapping to rename variables. Default is None.
        extra_dims:  str, or iterable of str, None
            Metadata key or list of metadata keys to use as additional dimensions on top of the
            predefined dimensions. Only enabled when no ``fixed_dims`` is specified. Default is None.
        drop_dims:  str, or iterable of str, None
            Metadata key or list of metadata keys to be ignored as dimensions. Default is None.
            Default is None.
        ensure_dims: str, or iterable of str, None
            Metadata key or list of metadata keys that should be used as dimensions even
            when ``squeeze=True``. Default is None.
        fixed_dims: str, or iterable of str, None
            Metadata key or list of metadata keys in the order they should be used as dimensions. When
            defined no other dimensions will be used. Might be incompatible with other settings.
            Default is None.
        dim_roles: dict
            Specify the "roles" used to form the predefined dimensions. The predefined dimensions are
            automatically generated when no ``fixed_dims`` specified and comprise the following
            (in a fixed order):

            - ensemble forecast member dimension
            - temporal dimensions (controlled by ``time_dim_mode``)
            - vertical dimensions (controlled by ``level_dim_mode``)

            ``dim_roles`` is a mapping between the "roles" and the metadata keys representing the roles.
            The possible roles are as follows:

            - "ens": metadata key interpreted as ensemble forecast members
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
                    "ens": "number",
                    "date": "dataDate",
                    "time": "dataTime",
                    "step": "step",
                    "forecast_reference_time": None,
                    "valid_date": None,
                    "level": "level",
                    "level_type": "typeOfLevel",
                }

            ``dims_roles`` behaves differently to the other kwargs in the sense that
            it does not override but update the default values. So e.g. to change only "ens" in
            the defaults it is enough to specify: "dim_roles={"ens": "perturbationNumber"}.
        rename_dims: dict, None
            Mapping to rename dimensions. Default is None.
        dims_as_attrs: str, or iterable of str, None
            Dimension or list of dimensions which should be turned to variable
            attributes if they have only one value for the given variable. Default is None.
        time_dim_mode: str
            Define how predefined temporal dimensions are formed. The possible values are as follows:

            - "forecast": adds two dimensions:

              - "forecast_reference_time": built from the "date" and "time" roles
                (see ``dim_roles``) as np.datetime64 values
              - "step": built from the "step" role. When ``decode_time=True`` the values are
                np.timedelta64
            - "valid_time": adds a dimension called "valid_time" as described by the "valid_time"
              role (see ``dim_roles``). Will contain np.datetime64 values,
            - "raw": the "date", "time" and "step" roles are turned into 3 separate dimensions
        level_dim_mode: str
            Define how predefined vertical dimensions are formed. The possible values are:

            - "level": adds a single dimension according to the "level" role (see ``dim_roles``)
            - "level_per_type": adds a separate dimensions for each level type based on the
              "level" and "level_type" roles.
            - "level_and_type": Use a single dimension for combined level and type of level.
        squeeze: bool
            Remove dimensions which has only one valid values. Not applies to dimension in
            ``ensure_dims``. Default is True.
        add_valid_time_coord: bool
            Add a `valid_time` coordinate containing np.datetime64 values to the
            dataset. Only can be used when ``add_valid_time_dim`` is False. Default is False.
        decode_time: bool
            Decode the datetime coordinates to datetime64 values, while step coordinates to timedelta64
            values. Default is True.
        add_geo_coords: bool
            Add geographic coordinates to the dataset when field values are represented by
            a single "values" dimension. Default is True.
        flatten_values: bool
            Flatten the values per field resulting in a single dimension called
            "values" representing a field. Otherwise the field shape is used to form
            the field dimensions. When the fields are defined on an unstructured grid (e.g.
            reduced Gaussian) or are spectral (e.g. spherical harmonics) this option is
            ignored and the field values are always represented by a single "values"
            dimension. Default is False.
        attrs_mode: str
            Define how attributes are generated. The possible values are:

            - "fixed": Use the attributes defined in ``variable_attrs`` as variables
              attributes and ``global_attrs`` as global attributes.
            - "unique": Use all the attributes defined in ``attrs``, ``variable_attrs``
              and ``global_attrs``. When an attribute has unique a value for a dataset
              it will be a global attribute, otherwise it will be a variable attribute.
              However keys in ``variable_attrs`` are always used as variable attributes,
              while keys in ``global_attrs`` are always used as global attributes.
        attrs: str or list, None
            List of metadata keys to use as attributes.
        variable_attrs: str or list, None
            Metadata key or keys to use as variable attributes. Default is None.
        global_attrs: , None
            Metadata key or keys to use as global attributes. Default is None.
        coord_attrs: dict, None
            To be documented. Default is None.
        rename_attrs: dict, None
            A dictionary of attribute to rename. Default is None.
        remapping: dict, None
            Define new metadata keys for indexing. Default is None.
        strict: bool
            Perform stricter checks on hypercube consistency. Default is True.
        errors: str, None
            How to handle errors. Default is None.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array data.
        array_module: module
            The module to use for array operations. Default is numpy.
        """
        _kwargs = dict(
            profile=profile,
            variable_key=variable_key,
            drop_variables=drop_variables,
            rename_variables=rename_variables,
            extra_dims=extra_dims,
            drop_dims=drop_dims,
            ensure_dims=ensure_dims,
            fixed_dims=fixed_dims,
            rename_dims=rename_dims,
            dim_roles=dim_roles,
            dims_as_attrs=dims_as_attrs,
            time_dim_mode=time_dim_mode,
            level_dim_mode=level_dim_mode,
            squeeze=squeeze,
            attrs_mode=attrs_mode,
            attrs=attrs,
            variable_attrs=variable_attrs,
            global_attrs=global_attrs,
            coord_attrs=coord_attrs,
            rename_attrs=rename_attrs,
            add_valid_time_coord=add_valid_time_coord,
            add_geo_coords=add_geo_coords,
            flatten_values=flatten_values,
            remapping=remapping,
            decode_time=decode_time,
            strict=strict,
            errors=errors,
            dtype=dtype,
            array_module=array_module,
        )

        fieldlist = self._fieldlist(filename_or_obj, source_type)

        if hasattr(fieldlist, "_ek_builder"):
            builder = fieldlist._ek_builder
            return builder.build()
        else:
            from .builder import SingleDatasetBuilder

            return SingleDatasetBuilder(fieldlist, **_kwargs).build()

    @classmethod
    def guess_can_open(cls, filename_or_obj):
        return True  # filename_or_obj.endswith(".grib")

    @staticmethod
    def _fieldlist(filename_or_obj, source_type):
        from earthkit.data.core import Base

        if isinstance(filename_or_obj, Base):
            ds = filename_or_obj
        # TODO: Add Path? or handle with try statement
        elif isinstance(filename_or_obj, str):
            from earthkit.data import from_source

            ds = from_source(source_type, filename_or_obj)
        else:
            from earthkit.data import from_object

            ds = from_object(filename_or_obj)
        return ds


def data_array_to_list(da):
    dims = [dim for dim in da.dims if dim not in ["values", "X", "Y", "lat", "lon"]]
    coords = {key: value for key, value in da.coords.items() if key in dims}

    data_list = []
    metadata_list = []
    for values in product(*[coords[dim].values for dim in dims]):
        local_coords = dict(zip(dims, values))
        xa_field = da.sel(**local_coords)

        # extract metadata from object
        if hasattr(da, "earthkit"):
            metadata = da.earthkit.metadata
        else:
            raise ValueError(
                "Earthkit attribute not found in DataArray. Required for conversion to FieldList!"
            )

        metadata = metadata.override(**local_coords)
        data_list.append(xa_field.values)
        metadata_list.append(metadata)
    return data_list, metadata_list


class XarrayEarthkit:
    def to_grib(self, filename):
        fl = self.to_fieldlist()
        fl.save(filename)


@xarray.register_dataarray_accessor("earthkit")
class XarrayEarthkitDataArray(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    # Making it not a property so it behaves like a regular earthkit metadata object
    @property
    def metadata(self):
        _metadata = self._obj.attrs.get("metadata", tuple())
        if len(_metadata) < 1:
            from earthkit.data.readers.netcdf import XArrayMetadata

            return XArrayMetadata(self._obj)
        if "id" == _metadata[0]:
            import ctypes

            return ctypes.cast(_metadata[1], ctypes.py_object).value
        elif "grib_handle" == _metadata[0]:
            from earthkit.data.readers.grib.codes import GribCodesReader
            from earthkit.data.readers.grib.metadata import GribMetadata

            handle = GribCodesReader.from_cache(_metadata[1]).at_offset(_metadata[2])
            return GribMetadata(handle)
        else:
            from earthkit.data.readers.netcdf import XArrayMetadata

            return XArrayMetadata(self._obj)

    # Corentin property method:
    # @property
    # def metadata(self):
    #     return self._obj.attrs.get("metadata", None)

    # @metadata.setter
    # def metadata(self, value):
    #     self._obj.attrs["metadata"] = value

    # @metadata.deleter
    # def metadata(self):
    #     self._obj.attrs.pop("metadata", None)

    def to_fieldlist(self):
        from earthkit.data import FieldList

        data_list, metadata_list = data_array_to_list(self._obj)
        field_list = FieldList.from_numpy(numpy.array(data_list), metadata_list)
        return field_list


@xarray.register_dataset_accessor("earthkit")
class XarrayEarthkitDataSet(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def to_fieldlist(self):
        from earthkit.data import FieldList

        data_list = []
        metadata_list = []
        for var in self._obj.data_vars:
            da = self._obj
            da_data, da_metadata = data_array_to_list(da)
            data_list.extend(da_data)
            metadata_list.extend(da_metadata)
        field_list = FieldList.from_numpy(numpy.array(data_list), metadata_list)
        return field_list
