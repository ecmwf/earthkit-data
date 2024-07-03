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
        variable_metadata_keys=None,
        variable_mapping=None,
        drop_variables=None,
        extra_index_keys=None,
        ignore_index_keys=None,
        dims=None,
        squeeze=True,
        flatten_values=False,
        remapping=None,
        profile="mars",
        base_datetime_dim=False,
        valid_datetime_dim=False,
        valid_datetime_coord=False,
        timedelta_step=False,
        level_and_type_dim=False,
        level_per_type_dim=False,
        geo_coords=True,
        merge_cf_and_pf=False,
        errors=None,
        array_module=numpy,
    ):
        r"""
        variable_key: str, None
            Metadata key to use for defining the dataset variables. It cannot be
            defined as a dimension. When None, the key is automatically determined.
        variable_metadata_keys: str, iterable of str, None
            Metadata keys to include as variable attributes in the dataset. When None, variable
            attributes are automatically generated.
        variable_mapping: str, dict, None
            Mapping to change variable names in the generated dataset. Variable names are defined
            by using the ``variable_keys`` metadata key. Whether this name is altered depends on the
            value of ``variable_mapping`:
            - None: the variable names are not altered
            - "auto": the names starting with a number are altered by placing the number
               at the end and adding the "m" suffix. E.g. "2t" -> "t2m"
            - dict: applies a mapping of the form {old_name: new_name}
            The default is None.
        drop_variables: str, or iterable of str, None
            A variable or list of variables to drop from the dataset. Default is None.
        extra_index_keys:  str, or iterable of str, None
            List of additional metadata keys to use as index keys. Only enabled when
            no ``dims`` is specified.
        ignore_index_keys:  str, or iterable of str, None
            List of metadata keys to ignore as index keys. Default is None.
        dims: str, or iterable of str, None
            Dimension or list of dimensions in the order they should be used. When defined
            no other dimensions will be used. Might be incompatible with some
            other options.
        squeeze: bool
            Remove dimensions which has one or zero valid values. Default is True.
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
            The profile to use for indexing the dataset. Default is "mars".
        base_datetime_dim: bool
            The ``date`` and ``time`` dimensions are combined into a single dimension
            called `base_datetime` with datetime64 values. Default is False.
        valid_datetime_dim: bool
            The ``date``, ``time`` and ``step`` dimensions are combined into a single
            dimension called `valid_datetime` with np.datetime64 values. Default is False.
        timedelta_step: bool
            Convert the ``step`` dimension to np.timedelta64 values. Default is False.
        valid_datetime_coord: bool
            Add a `valid_datetime` coordinate containing np.datetime64 values to the
            dataset. Only used when ``valid_datetime_dim`` is False. Default is False.
        level_and_type_dim: bool
            Use a single dimension for level and type of level. Cannot be used when
            ``_level_per_type_dim`` is True. Default is False.
        level_per_type_dim: bool
            Use a separate dimension for each level type.  Cannot be used when
            ``level_and_type_dim`` is True.  Default is False.
        merge_cf_and_pf: bool
            Treat ENS control forecasts as if they had "type=pf" and "number=0" metadata values.
            Default is False.
        geo_coords: bool
            Add geographic coordinates to the dataset when field values are represented by
            a single "values" dimension. Default is True.
        errors: str, None
            How to handle errors. Default is None.
        array_module: module
            The module to use for array operations. Default is numpy.
        """
        _kwargs = dict(
            variable_key=variable_key,
            variable_metadata_keys=variable_metadata_keys,
            variable_mapping=variable_mapping,
            drop_variables=drop_variables,
            extra_index_keys=extra_index_keys,
            ignore_index_keys=ignore_index_keys,
            dims=dims,
            squeeze=squeeze,
            flatten_values=flatten_values,
            remapping=remapping,
            profile=profile,
            base_datetime_dim=base_datetime_dim,
            valid_datetime_dim=valid_datetime_dim,
            valid_datetime_coord=valid_datetime_coord,
            timedelta_step=timedelta_step,
            level_and_type_dim=level_and_type_dim,
            level_per_type_dim=level_per_type_dim,
            geo_coords=geo_coords,
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
        print("CALLED")

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
