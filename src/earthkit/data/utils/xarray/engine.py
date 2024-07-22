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
        return SplitDatasetBuilder(ds, **backend_kwargs, **kwargs).build()


class EarthkitBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        source_type="file",
        variable_key=None,
        drop_variables=None,
        extra_variable_attrs=None,
        extra_global_attrs=None,
        extra_dims=None,
        drop_dims=None,
        ensure_dims=None,
        fixed_dims=None,
        dims_as_attrs=None,
        # squeeze=True,
        flatten_values=False,
        remapping=None,
        profile="mars",
        time_dim_mode="forecast",
        time_dim_mapping=None,
        add_valid_time_coord=False,
        decode_time=True,
        # step_as_timedelta=False,
        level_dim_mode="level",
        add_geo_coords=True,
        merge_cf_and_pf=False,
        errors=None,
        array_module=numpy,
    ):
        r"""
        variable_key: str, None
            Metadata key to use for defining the dataset variables. It cannot be
            defined as a dimension. When None, the key is automatically determined.
        drop_variables: str, or iterable of str, None
            A variable or list of variables to drop from the dataset. Default is None.
        extra_variable_attrs: str, iterable of str, None
            Metadata key or list of metadata keys to include as additional variable attributes
            on top of the automatically generated ones.
        extra_global_attrs: str, iterable of str, None
            Metadata key or list+_ of metadata keys to include as additional global attributes on top of
            the automatically generated ones. Default is None.
        extra_dims:  str, or iterable of str, None
            Metadata key or list of metadata keys to use as additional dimensions. Only enabled when
            no ``fixed_dims`` is specified. Default is None.
        drop_dims:  str, or iterable of str, None
            Metadata key or list of metadata keys to ignore as dimensions. Default is None.
        fixed_dims: str, or iterable of str, None
            Metadata key or list of metadata keys in the order they should be used as dimensions. When
            defined no other dimensions will be used. Might be incompatible with some
            other options. Default is None.
        ensure_dims: str, or iterable of str, None
            Metadata key or list of metadata keys that should be used as dimensions even
            when ``squeeze=True``. Default is None.
        dims_as_attrs: str, or iterable of str, None
            Dimension or list of dimensions which should be turned to variable metadata
            attributes if they have only one value for the given variable. Default is None.
            be used as va. Default is None.
        squeeze: bool
            Remove dimensions which has one or zero valid values. Not applies to dimension in
            ``ensure_dims``. Default is True.
        flatten_values: bool
            Flatten the values per field resulting in a single dimension called
            "values" representing a field. Otherwise the field shape is used to form
            the field dimensions. When the fields are defined on an unstructured grid (e.g.
            reduced Gaussian) or are spectral (e.g. spherical harmonics) this option is
            ignored and the field values are always represented by a single "values"
            dimension. Default is False.
        remapping: dict, None
            Define new metadata keys for indexing. Default is None.
        profile: str
            The profile to use for creating the dataset. Default is "mars".
        time_dim_mode: str
            The possible values are:

            - "forecast": The ``date`` and ``time`` dimensions are combined into a single dimension
              called `forecast_reference_time` with datetime64 values.
            - "valid_time": The ``date``, ``time`` and ``step`` dimensions are combined into a single
              dimension called `valid_time` with np.datetime64 values. Default is False.
            - "raw": The ``date``, ``time`` and "step" dimensions used.
        step_as_timedelta: bool
            Convert the ``step`` dimension to np.timedelta64 values. Default is False.
        decode_time: bool
            Decode the datetime coordinates to datetime64 values, while step coordinates to timedelta64
            values. Default is True.
        add_valid_time_coord: bool
            Add a `valid_time` coordinate containing np.datetime64 values to the
            dataset. Only can be used when ``add_valid_time_dim`` is False. Default is False.
        level_dim_mode: str
            The possible values are:

            - "level": Use a single dimension for level.
            - "level_per_type": Use a separate dimension for each level type.
            - "level_and_type": Use a single dimension for combined level and type of level.
        add_geo_coords: bool
            Add geographic coordinates to the dataset when field values are represented by
            a single "values" dimension. Default is True.
        errors: str, None
            How to handle errors. Default is None.
        array_module: module
            The module to use for array operations. Default is numpy.
        """
        _kwargs = dict(
            variable_key=variable_key,
            extra_variable_attrs=extra_variable_attrs,
            drop_variables=drop_variables,
            extra_global_attrs=extra_global_attrs,
            extra_dims=extra_dims,
            drop_dims=drop_dims,
            fixed_dims=fixed_dims,
            ensure_dims=ensure_dims,
            dims_as_attrs=dims_as_attrs,
            # squeeze=squeeze,
            flatten_values=flatten_values,
            remapping=remapping,
            profile=profile,
            time_dim_mode=time_dim_mode,
            time_dim_mapping=time_dim_mapping,
            decode_time=decode_time,
            add_valid_time_coord=add_valid_time_coord,
            # step_as_timedelta=step_as_timedelta,
            level_dim_mode=level_dim_mode,
            add_geo_coords=add_geo_coords,
            merge_cf_and_pf=merge_cf_and_pf,
            errors=errors,
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
