# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

# from earthkit.data.readers import netcdf
from earthkit.data.wrappers import Wrapper

LOG = logging.getLogger(__name__)


class XArrayDataArrayWrapper(Wrapper):
    """Wrapper around an xarray `DataArray`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    # def axis(self, axis):
    #     """
    #     Get the data along a specific coordinate axis.

    #     Parameters
    #     ----------
    #     axis : str
    #         The coordinate axis along which to extract data. Accepts values of
    #         `x`, `y`, `z` (vertical level) or `t` (time) (case-insensitive).

    #     Returns
    #     -------
    #     xarray.core.dataarray.DataArray
    #         An xarray `DataArray` containing the data along the given
    #         coordinate axis.
    #     """
    #     for coord in self.source.coords:
    #         if self.source.coords[coord].attrs.get("axis", "").lower() == axis:
    #             break
    #     else:
    #         candidates = AXES.get(axis, [])
    #         for coord in candidates:
    #             if coord in self.source.coords:
    #                 break
    #         else:
    #             raise ValueError(f"No coordinate found with axis '{axis}'")
    #     return self.source.coords[coord]

    def to_xarray(self, *args, **kwargs):
        """Return an xarray representation of the data.

        Returns
        -------
        xarray.core.dataarray.DataArray
        """
        return self.data

    def to_numpy(self, flatten=False):
        """Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        arr = self.data.to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_pandas(self, *args, **kwargs):
        """Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self.data.to_dataframe(*args, **kwargs)

    def to_netcdf(self, *args, **kwargs):
        """Save the data to a netCDF file.

        Parameters
        ----------
        See `xarray.DataArray.to_netcdf`.
        """
        return self.data.to_netcdf(*args, **kwargs)

    def _encode(self, encoder, **kwargs):
        """Encode the data using the specified encoder.

        Parameters
        ----------
        encoder : Encoder
            The encoder to use for encoding the data.
        **kwargs : dict
            Additional keyword arguments to pass to the encoder.

        Returns
        -------
        EncodedData
            The encoded data.
        """
        return encoder._encode_xarray(data=self.data, **kwargs)

    def convert_units(
        self,
        source_units: str | None = None,
        target_units: str | dict[str, str] | None = None,
        units_mapping: dict[str, str] | None = None,
    ):
        """Convert the units of the data.
        Parameters
        ----------
        source_units : str
            The source unit.
        target_units : str | dict[str, str]
            The target units, or a mapping of variables names to target units.
        units_mapping : dict[str, str]
            A mapping of source units to target units.

        Returns:
            xarray.DataArray with converted units.
        """

        if target_units is None and units_mapping is None:
            LOG.warning(
                "target_units or units_mapping must be provided for unit conversion for xarray.DataArray."
                "Not converting units."
            )
            return

        if source_units is None:
            # Try to get from attributes
            source_units = self.data.attrs.get("units", None)
            if source_units is None:
                LOG.warning(
                    "source_units must be provided for unit conversion if not present in data attributes."
                )
                return

        if target_units is None:
            target_units = units_mapping.get(source_units, None)

        elif isinstance(target_units, dict):
            # Get variable name
            var_name = self.data.name
            target_units = target_units.get(var_name, None)

        if target_units is None:
            LOG.warning(
                "Could not determine target_units for unit conversion for xarray.DataArray."
                "Not converting units."
            )
            return

        from earthkit.utils.units import convert

        output = self.data.copy()
        output.values = convert(output.values, source_units, target_units)
        output.attrs["units"] = target_units

        return output

    def update_metadata(self, *args, **kwargs):
        """Update the metadata of the DataArray.

        Parameters
        ----------
        *args : dict
            Positional arguments can be dictionaries, which are used to update
            the metadata.
        **kwargs : dict
            Keyword arguments can be used to update the metadata.

        Returns
        -------
        xarray.DataArray
            The data with updated metadata.

        """
        output = self.data.copy()
        for arg in args:
            if isinstance(arg, dict):
                output.attrs.update(arg)
        output.attrs.update(kwargs)
        return output

    # def validate_parameter_metadata(self, metadata_model: dict[str, dict] | None = None, **kwargs):
    #     """Validate and update the parameter metadata of the data according to the given metadata model.

    #     Parameters
    #     ----------
    #     metadata_model : dict[str, dict]
    #         The metadata model to use for validation and updating.

    #     """
    #     if metadata_model is None:
    #         return

    #     attrs = self.data.attrs
    #     for key, expected in metadata_model.items():
    #         if value := attrs.get(key, None) not in expected:
    #             LOG.warning(
    #                 f"Metadata key '{key}' has value '{value}', expected '{expected}'."
    #             )


class XArrayDatasetWrapper(XArrayDataArrayWrapper):
    """Wrapper around an xarray `DataSet`, offering polymorphism and convenience
    methods.
    """

    def to_numpy(self, flatten=False):
        """Return a numpy `ndarray` representation of the data.

        Returns
        -------
        numpy.ndarray
        """
        arr = self.data.to_array().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def convert_units(self, *args, **kwargs):
        """Convert the units of the data.
        Parameters
        ----------
        source_units : str
            The source unit.
        target_units : str | dict[str, str]
            The target units, or a mapping of variables names to target units.
        units_mapping : dict[str, str]
            A mapping of source units to target units.
        Returns:
            xarray.DataSet with converted units.
        """
        import xarray as xr

        output = xr.Dataset()
        for var in self.data.data_vars:
            var_wrapper = XArrayDataArrayWrapper(self.data[var])
            var_wrapper.convert_units(*args, **kwargs)
            output[var] = var_wrapper.data
        output.attrs = self.data.attrs

        return output

    def update_metadata(self, *args, **kwargs):
        """Update the metadata of the data according to the given metadata model."""
        return

    # def validate_parameter_metadata(self, metadata_model: dict[str, str | dict[str, str]] | None = None, **kwargs):
    #     """Validate and update the parameter metadata of the data according to the given metadata model.

    #     Parameters
    #     ----------
    #     metadata_model : dict[str, str | dict[str, str]] | None
    #         The metadata model to use for validation and updating. If None, no validation is performed.

    #     Returns
    #     -------
    #     xarray.DataArray
    #         The data with validated and updated parameter metadata.
    #     """
    #     if metadata_model is None:
    #         # LOG.warning(
    #         #     "metadata_model must be provided for parameter metadata validation for xarray.DataArray."
    #         #     "Not validating metadata."
    #         # )
    #         return

    #     for var in set(self.data.data_vars) & metadata_model.keys():
    #         attrs = self.data[var].attrs
    #         for key, expected in metadata_model[var].items():
    #             if value := attrs.get(key, None) not in expected:
    #                 LOG.warning(
    #                     f"Variable '{var}': metadata key '{key}' has value '{value}', expected '{expected}'."
    #                 )


def wrapper(data, *args, fieldlist=False, try_dataset=True, **kwargs):
    from earthkit.data.utils import is_module_loaded

    if not is_module_loaded("xarray"):
        return None

    import xarray as xr

    ds = None
    if isinstance(data, xr.Dataset):
        ds = data
    elif isinstance(data, xr.DataArray):
        if not try_dataset:
            return XArrayDataArrayWrapper(data, *args, **kwargs)
        try:
            ds = data.to_dataset()
        except ValueError:
            return XArrayDataArrayWrapper(data, *args, **kwargs)

    if ds is not None:
        if not fieldlist:
            return XArrayDatasetWrapper(ds, *args, **kwargs)

        from earthkit.data.readers.netcdf.fieldlist import XArrayFieldList

        fs = XArrayFieldList(ds, **kwargs)
        if fs.has_fields():
            return fs
        else:
            return XArrayDatasetWrapper(ds, *args, **kwargs)

    return None
