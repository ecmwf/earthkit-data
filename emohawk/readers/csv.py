# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import csv
import io
import mimetypes
import os
import zipfile

from emohawk.wrappers.pandas import PandasFrameWrapper

from . import Reader


class ZipProbe:
    def __init__(self, path, newline=None, encoding=None):
        zip = zipfile.ZipFile(path)
        members = zip.infolist()
        self.f = zip.open(members[0].filename)
        self.encoding = encoding

    def read(self, size):
        bytes = self.f.read(size)
        return bytes.decode(self.encoding)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        pass


def probe_csv(
    path,
    probe_size=4096,
    compression=None,
    for_is_csv=False,
    minimum_columns=2,
    minimum_rows=2,
):

    OPENS = {
        None: open,
        "zip": ZipProbe,
    }

    try:
        import gzip

        OPENS["gzip"] = gzip.open
    except ImportError:
        pass

    try:
        import bz2

        OPENS["bz2"] = bz2.open
    except ImportError:
        pass

    try:
        import lzma

        OPENS["lzma"] = lzma.open
    except ImportError:
        pass

    _open = OPENS[compression]

    try:
        with _open(path, newline="", encoding="utf-8") as f:
            sample = f.read(probe_size)
            sniffer = csv.Sniffer()
            dialect, has_header = sniffer.sniff(sample), sniffer.has_header(sample)

            if for_is_csv:
                # Check that it is not a trivial text file.
                reader = csv.reader(io.StringIO(sample), dialect)
                if has_header:
                    header = next(reader)
                    if len(header) < minimum_columns:
                        return None, False
                cnt = 0
                for row in reader:
                    cnt += 1
                    if cnt >= minimum_rows:
                        break

                if cnt < minimum_rows:
                    return None, False

            return dialect, has_header

    except UnicodeDecodeError:
        return None, False

    except csv.Error:
        return None, False


def is_csv(path, probe_size=4096, compression=None):

    _, extension = os.path.splitext(path)

    if extension in (".xml",):
        return False

    dialect, _ = probe_csv(path, probe_size, compression, for_is_csv=True)
    return dialect is not None


class CSVReader(Reader):
    """
    Class for reading and polymorphing CSV files.
    """

    def __init__(self, source, compression=None):
        super().__init__(source)
        self.compression = compression
        self.dialect, self.has_header = probe_csv(source, compression=compression)

    def _pandas_wrapper(self, **kwargs):
        import pandas

        pandas_read_csv_kwargs = kwargs.get("pandas_read_csv_kwargs", {})
        if self.compression is not None:
            pandas_read_csv_kwargs = dict(**pandas_read_csv_kwargs)
            pandas_read_csv_kwargs["compression"] = self.compression

        if self.dialect is not None:
            pandas_read_csv_kwargs["dialect"] = self.dialect

        return PandasFrameWrapper(
            pandas.read_csv(self.source, **pandas_read_csv_kwargs)
        )

    def to_pandas(self, **kwargs):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self._pandas_wrapper(**kwargs).to_pandas()

    def _to_xarray(self, *args, **kwargs):
        """
        Return an xarray representation of the data.

        Returns
        -------
        xarray.core.dataarray.DataArray
        """
        pandas_to_xarray_kwargs = kwargs.get("pandas_to_xarray_kwargs", {})
        return self._pandas_wrapper(**kwargs)._to_xarray(**pandas_to_xarray_kwargs)


def reader(path, magic, deeper_check, fwf=False):
    kind, compression = mimetypes.guess_type(path)

    if kind == "text/csv":
        return CSVReader(path, compression=compression)

    if deeper_check and False:
        if is_csv(path):
            return CSVReader(path)
