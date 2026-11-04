# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

r"""Encoder for the Metview geopoints (``#GEO``) and geopointset (``#GEOPOINTSET``) formats.

What it writes can always be read back with :py:func:`from_source`:

- a file read by the geopoints reader is copied to a file target as it is, without parsing it
  (this is what :meth:`GeopointsEncoder._encode_path` does);
- a featurelist is written block by block, keeping the format, the columns and the ``#METADATA``
  section of every block. Consecutive features of a row featurelist that come from the same block
  are merged into one block;
- a field or a fieldlist is written in the TRADITIONAL format, with one block per field. The
  ``latitude``, ``longitude`` and ``value`` columns come from the geography and the values of the
  field, ``level``, ``date`` and ``time`` from its metadata, and the name of the parameter becomes
  the ``param`` entry of ``#METADATA``. The name of the level type of the field, when it has one,
  becomes the ``level_type`` entry of ``#METADATA``;
- anything else raises :py:class:`NotImplementedError`.

A file with more than one block is written as a geopointset, a file with exactly one block as a
plain geopoints file.

Missing values (None, NaN, NaT) are written as ``3e+38``, the missing value of the format, which
the reader turns back into NaN. A text value that cannot be written as a whitespace separated
token raises :py:class:`ValueError`; the ``stnid`` column escapes a space as ``\32\`` and a tab
as ``\9\``, which is how the reader decodes them back.
"""

import functools
import io
import itertools
import logging
import math
from numbers import Integral, Real

import numpy as np

from earthkit.data.field.component.level_type import LevelTypes
from earthkit.data.readers.geopoints.parser import MISSING_VALUE

from . import EncodedData, Encoder, FilePathEncodedData

LOG = logging.getLogger(__name__)

#: The name of the encoder.
NAME = "geopoints"

#: Token written for a missing value; the reader parses it back into NaN.
MISSING_TOKEN = f"{MISSING_VALUE:g}"

#: Format written without a ``#FORMAT`` line, because the reader defaults to it.
TRADITIONAL = "TRADITIONAL"

#: The columns a field is written with (the TRADITIONAL format).
FIELD_COLUMNS = ["latitude", "longitude", "level", "date", "time", "value"]

#: The value of a missing ``stnid``.
_STNID_MISSING = "?"

#: The escapes the reader decodes in the ``stnid`` column.
_STNID_ESCAPES = ((" ", "\\32\\"), ("\t", "\\9\\"))


def _is_missing(x):
    """Return True for the values that are missing in a column: None, NaN and NaT."""
    if x is None:
        return True
    try:
        # NaN and NaT are the only values that are not equal to themselves
        return bool(x != x)
    except (TypeError, ValueError):
        return False


def _number_token(x):
    """Format a number so that the reader parses it back exactly."""
    if isinstance(x, Integral) and not isinstance(x, bool):
        return str(int(x))
    x = float(x)
    if math.isnan(x) or x == MISSING_VALUE:
        # the reader turns the missing value into NaN, so writing it as is would keep NaN
        return MISSING_TOKEN
    if math.isfinite(x) and x.is_integer() and abs(x) < 1e16:
        # an integral value is written as an integer, the reader gives back the same number
        return str(int(x))
    # the shortest representation that parses back to the very same float
    return repr(x)


def _text_token(x, stnid=False):
    """Format a value of a column that can hold text, e.g. ``stnid`` or a ``value`` column."""
    if _is_missing(x):
        return _STNID_MISSING if stnid else MISSING_TOKEN
    if isinstance(x, (Integral, Real)) and not isinstance(x, (bool, np.bool_)):
        # an object column can mix numbers and text
        return _number_token(x)
    s = str(x)
    if stnid:
        if "\\" in s:
            raise ValueError(f"cannot write the geopoints stnid {x!r}: a backslash cannot be escaped")
        for char, escape in _STNID_ESCAPES:
            s = s.replace(char, escape)
    if not s or any(c.isspace() for c in s):
        raise ValueError(f"cannot write {x!r} as a geopoints value: it is not a whitespace free token")
    return s


_TEXT_TOKEN = functools.partial(_text_token, stnid=True)


def _to_timestamp(x):
    """Convert a date value into a :py:class:`pandas.Timestamp`, or None when it is missing."""
    if _is_missing(x):
        return None
    import pandas as pd

    try:
        ts = pd.Timestamp(x)
    except (TypeError, ValueError, OverflowError):
        return None
    return None if pd.isna(ts) else ts


def _date_numbers(values, field):
    """Return the YYYYMMDD (``field="date"``) or HHMM numbers of the date values, NaN when missing.

    The reader merges the ``time`` column of a block into its ``date`` column; this takes the two
    columns back out of the merged datetimes.
    """
    import pandas as pd

    a = np.asarray(values)
    if a.dtype == np.dtype("M8"):
        # a datetime64 without a unit (e.g. a bare NaT) needs one to become an index
        a = a.astype("datetime64[ns]")
    index = pd.DatetimeIndex(a.reshape(-1))
    missing = np.asarray(index.isna())

    def _part(name):
        return np.asarray(getattr(index, name), dtype="float64")

    if field == "date":
        parts = _part("year") * 10000 + _part("month") * 100 + _part("day")
    else:
        parts = _part("hour") * 100 + _part("minute")
    # a missing date is NaN, which _number_token() writes as the missing value
    return np.where(missing, np.nan, parts)


def _metadata_token(value, what):
    """Format one ``#METADATA`` key or value; the reader reads it back as an int, a float or a str."""
    if isinstance(value, (bool, np.bool_)):
        s = "1" if value else "0"
    elif isinstance(value, Integral):
        s = str(int(value))
    elif isinstance(value, Real):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"cannot write the geopoints metadata {what}={value!r}: it is not a number")
        s = _number_token(value)
    else:
        s = str(value)
    if not s or "=" in s or any(c in s for c in "\r\n"):
        raise ValueError(
            f"cannot write the geopoints metadata {what}={value!r}: a #METADATA line holds one "
            '"name=value" pair on a single line'
        )
    return s


def _is_binary(f):
    """Tell whether the file-like object ``f`` must be written with bytes."""
    mode = getattr(f, "mode", None)
    if isinstance(mode, str):
        return "b" in mode
    return not isinstance(f, io.TextIOBase)


class _Block:
    """One ``#GEO`` block: a format, its columns, its ``#METADATA`` section and its rows.

    Parameters
    ----------
    format: str
        One of "TRADITIONAL", "XYV", "XY_VECTOR", "POLAR_VECTOR" and "NCOLS".
    columns: list of str
        The column names, in the order of the tokens in a row.
    metadata: dict
        The ``#METADATA`` section.
    data: :py:class:`pandas.DataFrame` or dict
        The rows. A dict maps a column name to a 1-D array-like or to a scalar, which is then
        written on every row.
    n: int, None
        The number of rows. Guessed from ``data`` when None.
    """

    def __init__(self, format, columns, metadata, data, n=None):
        self.format = format
        self.columns = list(columns)
        self.metadata = dict(metadata)

        if hasattr(data, "columns"):
            # a DataFrame: use its columns as arrays. It is only read, never modified.
            frame = data
            data = {name: frame[name].to_numpy() for name in frame.columns}
            n = len(frame) if n is None else n

        if n is None:
            n = 0
            for value in data.values():
                if np.ndim(value) > 0:
                    n = max(n, np.asarray(value).size)
        self.n = int(n)

        self._cols = [self._column(name, data) for name in self.columns]

    def _column(self, name, data):
        """Return the (token function, values, written on every row) triple of one column."""
        if name not in data:
            if name == "time" and "date" in data:
                # the reader merged the time of the block into its date column
                numbers = _date_numbers(data["date"], "time")
                return _number_token, numbers, numbers.size == 1 and self.n > 1
            # a column the data does not have is missing on every row
            LOG.warning("geopoints: the column %r is missing from the data, writing it as missing", name)
            return _number_token, np.full(self.n, np.nan), False

        a = np.asarray(data[name]).reshape(-1)
        every_row = a.size == 1 and self.n > 1
        if a.dtype.kind == "M":
            numbers = _date_numbers(a, "time" if name == "time" else "date")
            return _number_token, numbers, numbers.size == 1 and self.n > 1
        if name == "stnid":
            return _TEXT_TOKEN, a, every_row
        if a.dtype == object or a.dtype.kind in "US":
            return _text_token, a, every_row
        return _number_token, a, every_row

    def header(self):
        """Yield the lines of the block before its rows."""
        yield "#GEO"
        if self.format != TRADITIONAL:
            yield f"#FORMAT {self.format}"
        if self.format == "NCOLS":
            yield "#COLUMNS"
            yield " ".join(self.columns)
        if self.metadata:
            yield "#METADATA"
            for key, value in self.metadata.items():
                yield f"{_metadata_token(key, 'key')}={_metadata_token(value, 'value')}"
        yield "#DATA"

    def rows(self):
        """Yield the data lines of the block."""
        if self.n == 0:
            return

        columns = []
        for token, values, every_row in self._cols:
            if every_row:
                columns.append(itertools.repeat(token(values[0]), self.n))
            else:
                # map() binds the token function now, a generator expression would not
                columns.append(map(token, values))

        for tokens in zip(*columns):
            yield " ".join(tokens)


class GeopointsEncodedData(EncodedData):
    """Geopoints data to write.

    Parameters
    ----------
    blocks: iterable of :class:`_Block`
        The blocks to write. They are consumed once, so when ``blocks`` is a generator the encoded
        data can only be written once.
    num_blocks: int, None
        The number of blocks when it is known; it only decides whether the file starts with the
        ``#GEOPOINTSET`` line. When None, ``blocks`` is turned into a list.
    """

    def __init__(self, blocks, num_blocks=None):
        self.blocks = blocks
        self.num_blocks = num_blocks

    def _lines(self):
        blocks = self.blocks
        if self.num_blocks is None:
            blocks = list(blocks)
            num = len(blocks)
        else:
            num = self.num_blocks

        if num != 1:
            # more or less than one block can only be a geopointset
            yield "#GEOPOINTSET"
        for block in blocks:
            yield from block.header()
            yield from block.rows()

    def to_bytes(self):
        out = io.BytesIO()
        self.to_file(out)
        return out.getvalue()

    def to_file(self, f, **kwargs):
        binary = _is_binary(f)
        for line in self._lines():
            line += "\n"
            f.write(line.encode("utf-8") if binary else line)

    def get(self, key, default=None):
        raise NotImplementedError


def _feature_block(feature, metadata):
    """Return the :class:`_Block` of a block feature."""
    try:
        block = feature.block
    except AttributeError:
        raise NotImplementedError(
            f"Cannot encode a {type(feature).__name__} as geopoints: only the features of a "
            "geopoints featurelist can be written"
        ) from None
    # the frame is only read, so the parser's own one can be used instead of a copy
    return _Block(block.format, block.columns, {**block.metadata, **metadata}, block._frame)


def _row_block(block, rows, metadata):
    """Return the :class:`_Block` with the rows ``rows`` of the parsed block ``block``."""
    frame = block._frame  # only read, never modified
    if all(b == a + 1 for a, b in zip(rows, rows[1:])):
        frame = frame.iloc[rows[0] : rows[-1] + 1]
    else:
        frame = frame.iloc[rows]
    return _Block(block.format, block.columns, {**block.metadata, **metadata}, frame)


def _featurelist_blocks(features, metadata):
    """Return the list of the :class:`_Block` objects of the geopoints features ``features``.

    Consecutive row features of the same block are written as one block.
    """
    blocks = []
    rows = None  # [block, the positions of its rows]

    for feature in features:
        block = getattr(feature, "block", None)
        if block is not None and hasattr(feature, "row"):
            # a row feature
            if rows is not None and rows[0] is block:
                rows[1].append(feature.row)
                continue
            if rows is not None:
                blocks.append(_row_block(*rows, metadata))
            rows = [block, [feature.row]]
            continue

        if rows is not None:
            blocks.append(_row_block(*rows, metadata))
            rows = None
        blocks.append(_feature_block(feature, metadata))

    if rows is not None:
        blocks.append(_row_block(*rows, metadata))
    return blocks


def _as_datetime64(value):
    """Convert a date-like value into :py:class:`numpy.datetime64`; NaT when it is missing."""
    if _is_missing(value):
        return np.datetime64("NaT", "ns")
    if isinstance(value, np.datetime64):
        return value
    ts = _to_timestamp(value)
    return np.datetime64("NaT", "ns") if ts is None else ts.to_datetime64()


def _field_block(field, metadata):
    """Return the :class:`_Block` of a field, written in the TRADITIONAL format."""
    geography = field.geography
    latitudes = geography.latitudes()
    longitudes = geography.longitudes()
    if latitudes is None or longitudes is None:
        raise ValueError(
            f"cannot write a field with {type(geography).__name__} geography as geopoints: "
            "it has no latitudes and longitudes"
        )

    lat = np.asarray(latitudes, dtype="float64").reshape(-1)
    lon = np.asarray(longitudes, dtype="float64").reshape(-1)
    values = np.asarray(field.to_numpy(flatten=True), dtype="float64").reshape(-1)
    if not (lat.size == lon.size == values.size):
        raise ValueError(
            f"cannot write a field as geopoints: {values.size} values but "
            f"{lat.size} latitudes and {lon.size} longitudes"
        )

    level = field.get("vertical.level", default=None)
    date = _as_datetime64(field.get("time.valid_datetime", default=None))

    metadata = dict(metadata)
    if "param" not in metadata:
        param = field.get("parameter.variable", default=None)
        if param is None:
            param = field.get("metadata.param", default=None)
        if param is not None:
            metadata["param"] = str(param)

    if "level_type" not in metadata:
        # a field without a level type, or with the unknown one, gets no entry
        level_type = field.get("vertical.level_type", default=None)
        if level_type is not None and str(level_type) != LevelTypes.UNKNOWN.value.name:
            metadata["level_type"] = str(level_type)

    data = {
        "latitude": lat,
        "longitude": lon,
        "level": np.nan if level is None else level,
        "date": date,
        "time": date,
        "value": values,
    }
    return _Block(TRADITIONAL, FIELD_COLUMNS, metadata, data, n=values.size)


class GeopointsEncoder(Encoder):
    """Encode data in the Metview geopoints format.

    Parameters
    ----------
    metadata: dict, None
        Entries added to the ``#METADATA`` section of every block that is written. When the block
        already has an entry with the same name, the one given here wins. A file that is copied as
        it is cannot take any metadata, so passing any makes the data be re-encoded.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        metadata=None,
        template=None,
        **kwargs,
    ):
        if data is None:
            raise ValueError("No data to encode")
        if template is not None:
            raise NotImplementedError("The geopoints encoder does not use a template")
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise NotImplementedError(f"The geopoints encoder has no option {names}")

        from earthkit.data.readers.geopoints.featurelist import GeopointsFeature, GeopointsRowFeature

        if isinstance(data, (GeopointsFeature, GeopointsRowFeature)):
            return self._encode_featurelist([data], target=target, metadata=metadata)

        if metadata is None:
            metadata = {}

        # copying a file as it is would ignore the metadata, so it is only allowed without any
        path_allowed = target is not None and target._name == "file" and not metadata and not self.metadata
        hints = {"path_allowed": path_allowed}

        from earthkit.data.data.wrappers import ObjectWrapperData, from_object

        wrapped = from_object(data)
        if isinstance(wrapped, ObjectWrapperData) or not hasattr(wrapped, "_encode"):
            # an object the library cannot dispatch an encoding for, e.g. a pandas DataFrame
            raise NotImplementedError(
                f"Cannot encode a {type(data).__name__} as geopoints: use a geopoints file, "
                "a featurelist, a field or a fieldlist"
            )
        return wrapped._encode(self, hints=hints, target=target, metadata=metadata, **kwargs)

    def _encode(self, data, *, target=None, **kwargs):
        raise NotImplementedError(f"Cannot encode a {type(data).__name__} as geopoints")

    def _encode_field(self, field, *, target=None, metadata=None, **kwargs):
        return GeopointsEncodedData([_field_block(field, self._metadata(metadata))], 1)

    def _encode_fieldlist(self, fieldlist, *, target=None, metadata=None, **kwargs):
        extra = self._metadata(metadata)
        try:
            num_blocks = len(fieldlist)
        except TypeError:
            num_blocks = None
        return GeopointsEncodedData((_field_block(f, extra) for f in fieldlist), num_blocks)

    def _encode_featurelist(self, featurelist, *, target=None, metadata=None, **kwargs):
        blocks = _featurelist_blocks(featurelist, self._metadata(metadata))
        return GeopointsEncodedData(blocks, len(blocks))

    def _encode_xarray(self, data, *, target=None, **kwargs):
        raise NotImplementedError("Cannot encode xarray data as geopoints")

    def _encode_path(self, path_info, *, target=None, **kwargs):
        # Write the file as is when it is a geopoints file and the target is a file. The copy is
        # made in binary mode, although a geopoints file is a text file for the reader: this way
        # it is byte identical, without any newline translation or decoding.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == NAME
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=True)
        return None

    def _metadata(self, metadata):
        """Return the ``#METADATA`` entries to add: the ones of the encoder then the ones given."""
        if not self.metadata and not metadata:
            return {}
        return {**self.metadata, **(metadata or {})}


encoder = GeopointsEncoder
