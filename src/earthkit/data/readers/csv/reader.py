# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from .. import Reader

LOG = logging.getLogger(__name__)


class CSVReader(Reader):
    r"""Class representing CSV data"""

    def __init__(self, source, path, compression=None):
        from . import probe_csv

        super().__init__(source, path)
        self.compression = compression
        self.dialect, self.has_header = probe_csv(path, compression=compression)

    def to_pandas(self, comment="#", pandas_read_csv_kwargs=None, **kwargs):
        """Convert CSV data into a :py:class:`pandas.DataFrame` using :py:func:`pandas.read_csv`.

        Please note that Earthkit should be able to handle compressed file objects.

        Parameters
        ----------
        comment: str
            Character that represents a comment line in csv file. This value is ignored if the comment
            character is defined in pandas_read_csv_kwargs.
        pandas_read_csv_kwargs: dict
            kwargs passed to :func:`pandas.read_csv`, this is used for safe parsing of kwargs via intermediate
            methods

        Returns
        -------
        :py:class:`pandas.DataFrame`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "data_with_comments.csv")
        >>> df = ds.to_pandas(pandas_read_csv_kwargs={"comment": "#"})

        """
        import pandas

        if pandas_read_csv_kwargs is None:
            pandas_read_csv_kwargs = {}

        if comment is not None:
            pandas_read_csv_kwargs.setdefault("comment", comment)

        if self.compression is not None:
            # Over-write any specified compression in the read kwargs
            pandas_read_csv_kwargs["compression"] = self.compression

        LOG.debug("pandas.read_csv(%s,%s)", self.path, pandas_read_csv_kwargs)
        return pandas.read_csv(self.path, **pandas_read_csv_kwargs)

    def to_xarray(self, pandas_read_csv_kwargs=None, **kwargs):
        """Convert CSV data into an xarray object`.

        First, the data is converted into a :py:class:`pandas.DataFrame` with :py:func:`pandas.read_csv`,
        then :py:meth:`pandas.DataFrame.to_xarray` is called to generate the xarray object.

        Parameters
        ----------
        pandas_read_csv_kwargs: dict
            kwargs passed to :py:func:`pandas.read_csv`.

        Returns
        -------
        Xarray object

        """
        return self.to_pandas(pandas_read_csv_kwargs=pandas_read_csv_kwargs).to_xarray(**kwargs)

    def to_data_object(self):
        from .data import CSVData

        return CSVData(self)
