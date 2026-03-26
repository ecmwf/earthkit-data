# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .source import SourceData


class GribData(SourceData):
    """
    Represent GRIB data.

    GRIB is the WMO's format for binary gridded data consisting of GRIB messages, which are represented
    as Fields in earthkit-data. The earthkit-data GRIB interface is based on :xref:`eccodes` and can handle
    both GRIB `edition 1 <https://community.wmo.int/activity-areas/wmo-codes/manual-codes/grib-edition-1>`_ and
    `edition 2 <https://library.wmo.int/index.php?lvl=notice_display&id=10684>`_.
    """

    _TYPE_NAME = "GRIB"

    @property
    def available_types(self):
        return [self._FIELDLIST, self._PANDAS, self._XARRAY, self._NUMPY, self._ARRAY]

    def describe(self):
        return f"GRIB data from {self._reader.path}"

    def __repr__(self):
        return "GribData(path={self._reader.path})"

    def to_fieldlist(self, *args, **kwargs):
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments to pass to the reader's to_xarray method.
            Please see :py:meth:`earthkit.data.data.FieldList.to_xarray` for details
            on the supported keyword arguments.

        """
        return self._reader.to_xarray(**kwargs)

    def to_numpy(self, *args, **kwargs):
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        return self._reader.to_array(*args, **kwargs)

    def _repr_html_(self):
        from earthkit.data.utils.summary import make_data_repr_html

        return make_data_repr_html(title="GRIB file", path=self._reader.path, types=self.available_types)
