# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Pure-Python parser for Metview geopoints and geopointset files.

The parsing rules follow Metview's C++ reader (``MvGeopoints.cc``). Each geopoints block is
turned into a :class:`pandas.DataFrame` laid out like the one returned by Metview's
``to_dataframe()``.
"""

import csv
import io
import math
import re
import warnings
from array import array

import numpy as np

#: Missing value used in geopoints files.
MISSING_VALUE = 3.0e38

#: Column names (as in Metview) of the fixed formats.
_FIXED_COLUMNS = {
    "TRADITIONAL": ["latitude", "longitude", "level", "date", "time", "value"],
    "XYV": ["longitude", "latitude", "value"],
    "XY_VECTOR": ["latitude", "longitude", "level", "date", "time", "x-comp", "y-comp"],
    "POLAR_VECTOR": ["latitude", "longitude", "level", "date", "time", "magnitude", "angle"],
}

#: Names that are coordinate columns in the NCOLS format. Any other name is a value column.
_NCOLS_COORDINATES = ("latitude", "longitude", "level", "elevation", "date", "time", "stnid")

#: Column names of the NCOLS format when there is no ``#COLUMNS`` section.
_NCOLS_DEFAULT_COLUMNS = ["stnid", "latitude", "longitude", "level", "date", "time", "elevation"]

#: Formats where the last column can contain text.
_TEXT_VALUE_FORMATS = ("TRADITIONAL", "XYV")

_INT_RE = re.compile(r"[+-]?[0-9]+")

#: What Metview (``_stringOrNumber()``) accepts as a number: an optional sign, digits with an
#: optional decimal point (``5``, ``5.``, ``5.25``, ``.5``; at least one digit) and an optional
#: exponent (``e`` or ``E``, optional sign, at least one digit). Everything else is text.
_NUMBER_PATTERN = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"


class GeopointsBlock:
    """One geopoints block, i.e. the content of a ``#GEO`` file or one member of a geopointset.

    The parameters are available as attributes of the same name.

    Parameters
    ----------
    format: str
        One of "TRADITIONAL", "XYV", "XY_VECTOR", "POLAR_VECTOR" and "NCOLS".
    columns: list of str
        Metview column names in file order. ``time`` is included where it exists and ``stnid`` is
        included for NCOLS (it is added as the first column when the file does not have it).
    metadata: dict
        Content of the ``#METADATA`` section with values converted to int, float or str.
    frame: :class:`pandas.DataFrame`
        The points of the block, returned (as a copy) by :meth:`to_pandas`.
    """

    def __init__(self, format, columns, metadata, frame):
        self.format = format
        self.columns = columns
        self.metadata = metadata
        self._frame = frame

    def to_pandas(self):
        """Return the block as a new :class:`pandas.DataFrame`."""
        return self._frame.copy()

    def __len__(self):
        return len(self._frame)

    def __repr__(self):
        return f"{self.__class__.__name__}(format={self.format!r}, columns={self.columns!r}, rows={len(self)})"


class GeopointsFile:
    """The result of parsing a geopoints or geopointset file.

    The parameters are available as attributes of the same name.

    Parameters
    ----------
    path: str
        Path of the file.
    is_set: bool
        True when the file is a geopointset (it starts with ``#GEOPOINTSET``).
    blocks: list of :class:`GeopointsBlock`
        The geopoints blocks. A plain geopoints file has one.
    """

    def __init__(self, path, is_set, blocks):
        self.path = path
        self.is_set = is_set
        self.blocks = blocks

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path!r}, is_set={self.is_set}, blocks={len(self.blocks)})"


def parse_geopoints(path):
    """Parse a geopoints or geopointset file.

    Parameters
    ----------
    path: str or path-like
        Path to the file.

    Returns
    -------
    :class:`GeopointsFile`

    Raises
    ------
    ValueError
        When the file content cannot be parsed. The message contains the file name.
    """
    path = str(path)
    blocks = []
    builder = None
    is_set = False

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\r\n")
            if lineno == 1:
                is_set = line.startswith("#GEOPOINTSET")

            if line.startswith("#GEO") and not line.startswith("#GEOPOINTSET"):
                if builder is not None:
                    blocks.append(builder.build())
                builder = _BlockBuilder(path)
                continue

            if builder is None:
                if is_set:
                    # only the #GEOPOINTSET line (and anything else) before the first block
                    continue
                # Metview does not require the first line to be "#GEO"
                builder = _BlockBuilder(path)

            builder.add_line(line, lineno)

    if builder is not None:
        blocks.append(builder.build())

    return GeopointsFile(path, is_set, blocks)


def _convert_metadata_value(v):
    if _INT_RE.fullmatch(v):
        return int(v)
    if "_" not in v:
        try:
            x = float(v)
        except ValueError:
            return v
        if math.isfinite(x):
            return x
    return v


class _BlockBuilder:
    """Collect the lines of one block and build the :class:`GeopointsBlock`."""

    def __init__(self, path):
        self.path = path
        self.format = "TRADITIONAL"
        self.metadata = {}
        self.ncols_names = None
        self.in_data = False
        self._expect_columns = False
        self._in_metadata = False
        self._in_db_info = False
        self.lines = []
        self.linenos = array("q")

    def add_line(self, line, lineno):
        if self.in_data:
            if line[:1] != "#" and len(line) > 4:
                self.lines.append(line)
                self.linenos.append(lineno)
            return

        if line.startswith("#DATA"):
            self.in_data = True
        elif line.startswith("#FORMAT "):
            self._set_format(line[7:].lstrip(" "))
        elif line.startswith("#COLUMNS"):
            self._expect_columns = True
        elif self._expect_columns:
            # the line following #COLUMNS holds the column names, whatever it is
            self.ncols_names = line.split()
            self._expect_columns = False
        elif line.startswith("#METADATA"):
            self._in_metadata = True
            self._in_db_info = False
        elif line.startswith("#DB_INFO"):
            self._in_db_info = True
            self._in_metadata = False
        elif self._in_metadata:
            self._add_metadata(line)
        # everything else in the header is ignored

    def _set_format(self, name):
        if name.startswith("POLAR_VECTOR"):
            self.format = "POLAR_VECTOR"
        elif name.startswith("XY_VECTOR"):
            self.format = "XY_VECTOR"
        elif name.startswith("XYV") or name.startswith("LLV"):
            self.format = "XYV"
        elif name.startswith("NCO"):
            self.format = "NCOLS"
        else:
            warnings.warn(
                f"{self.path}: unknown geopoints format {name.strip()!r}, using {self.format}",
                UserWarning,
            )

    def _add_metadata(self, line):
        parts = [p for p in line.split("=") if p]
        if len(parts) == 2:
            self.metadata[parts[0].strip(" ")] = _convert_metadata_value(parts[1].strip(" "))

    def build(self):
        if self.format == "NCOLS":
            columns, frame = self._build_ncols()
        else:
            columns = list(_FIXED_COLUMNS[self.format])
            frame = self._build_fixed(columns)
        return GeopointsBlock(self.format, columns, self.metadata, frame)

    def _error(self, msg, lineno=None):
        where = f"{self.path}" if lineno is None else f"{self.path}, line {lineno}"
        return ValueError(f"Error parsing geopoints file {where}: {msg}")

    # -- fixed formats -------------------------------------------------------------------------

    def _build_fixed(self, columns):
        n_expected = len(columns)
        if not self.lines:
            return _assemble(columns, None, 0, self.format in _TEXT_VALUE_FORMATS)

        counts = _token_counts(self.lines)
        short = np.flatnonzero(counts < n_expected)
        if short.size:
            i = short[0]
            raise self._error(
                f"expected {n_expected} values in {self.format} row, found {counts[i]}",
                self.linenos[i],
            )

        # extra trailing tokens are ignored
        for i in np.flatnonzero(counts > n_expected):
            self.lines[i] = " ".join(self.lines[i].split()[:n_expected])

        dtypes = {i: "float64" for i in range(n_expected)}
        if self.format in _TEXT_VALUE_FORMATS:
            # The value column may hold text. It is always read as text, because the float parser
            # accepts spellings (inf, nan, ...) which are text for Metview. See _text_or_float().
            dtypes[n_expected - 1] = str
        raw = self._read_table(n_expected, dtypes)
        return _assemble(columns, raw, len(self.lines), self.format in _TEXT_VALUE_FORMATS)

    # -- NCOLS ---------------------------------------------------------------------------------

    def _build_ncols(self):
        names = list(self.ncols_names) if self.ncols_names is not None else list(_NCOLS_DEFAULT_COLUMNS)

        n_coords = 0
        in_values = False
        for name in names:
            if name in _NCOLS_COORDINATES:
                if in_values:
                    raise self._error(
                        f"in the #COLUMNS line all coordinate columns must come before the value columns: {name}"
                    )
                n_coords += 1
            else:
                in_values = True

        if "latitude" not in names or "longitude" not in names:
            raise self._error("NCOLS geopoints must contain latitude and longitude columns")

        if len(set(names)) != len(names):
            raise self._error(f"duplicate column names in #COLUMNS line: {names}")

        n_named_values = len(names) - n_coords

        if not self.lines:
            # no data: the value columns are the named ones
            columns = names
            frame_columns = names
            raw = None
            n = 0
        else:
            counts = _token_counts(self.lines)
            n_tokens = int(counts[0])
            bad = np.flatnonzero(counts != n_tokens)
            if bad.size:
                i = bad[0]
                raise self._error(
                    f"different numbers of columns: {counts[i]} instead of {n_tokens} as in the first row",
                    self.linenos[i],
                )
            n_values = n_tokens - n_coords
            if n_values < 0:
                raise self._error(
                    f"{n_tokens} values in the first row but there are {n_coords} coordinate columns",
                    self.linenos[0],
                )
            if n_named_values > n_values:
                raise self._error(
                    f"{n_named_values} value columns named in #COLUMNS line but the data has only {n_values}",
                    self.linenos[0],
                )
            columns = names + [f"_v{i + 1}" for i in range(n_values - n_named_values)]
            # the generated names must not clash with the ones given in the #COLUMNS line
            # (Metview does not check this, the later column would silently replace the earlier)
            if len(set(columns)) != len(columns):
                dup = sorted({c for c in columns if columns.count(c) > 1})
                raise self._error(
                    f"duplicate column names {dup} after adding the names generated for the unnamed "
                    f"value columns (_v1, _v2, ...): {columns}"
                )
            frame_columns = columns

            dtypes = {i: "float64" for i in range(n_tokens)}
            if "stnid" in columns:
                dtypes[columns.index("stnid")] = str
            raw = self._read_table(n_tokens, dtypes)
            n = len(self.lines)

        has_stnid = "stnid" in columns
        frame = _assemble(frame_columns, raw, n, False)
        if not has_stnid:
            frame.insert(0, "stnid", np.full(n, None, dtype=object))
            columns = ["stnid"] + columns
        return columns, frame

    # -- reading -------------------------------------------------------------------------------

    def _read_table(self, n_tokens, dtypes):
        import pandas as pd

        text = "\n".join(self.lines)
        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=r"\s+",
                header=None,
                names=list(range(n_tokens)),
                dtype=dtypes,
                na_filter=False,
                quoting=csv.QUOTE_NONE,
                float_precision="round_trip",
                engine="c",
            )
        except (ValueError, TypeError) as e:
            raise self._error(f"cannot read the data values ({e})") from e
        return [df[i].to_numpy() for i in range(n_tokens)]


def _token_counts(lines):
    return np.fromiter((len(line.split()) for line in lines), dtype=np.int64, count=len(lines))


# -- DataFrame construction ----------------------------------------------------------------------


def _assemble(columns, raw, n, text_value):
    """Build the DataFrame from the raw column arrays.

    Parameters
    ----------
    columns: list of str
        Metview column names, one for each element of ``raw``.
    raw: list of ndarray or None
        Column data as read from the file. None means no data rows.
    n: int
        Number of rows.
    text_value: bool
        When True the last column can contain text (``raw`` holds it as str).
    """
    import pandas as pd

    data = {}
    if raw is None:
        raw = [None] * len(columns)
    values = dict(zip(columns, raw))

    time = _numeric(values["time"], n) if "time" in values else None

    for name in columns:
        col = values[name]
        if name == "stnid":
            data[name] = _decode_stnid(col)
        elif name == "date":
            data[name] = _make_datetime(_numeric(col, n), time)
        elif name == "time":
            # merged into "date" when there is one
            if "date" not in values:
                data[name] = _integer_if_possible(time)
        elif text_value and name == columns[-1]:
            data[name] = _text_or_float(col, n)
        else:
            data[name] = _numeric(col, n)

    return pd.DataFrame(data, columns=list(data), index=pd.RangeIndex(n))


def _numeric(col, n):
    """Return a float64 array with the missing value replaced by NaN."""
    if col is None:
        return np.empty(0, dtype="float64")
    a = np.array(col, dtype="float64")
    a[a == MISSING_VALUE] = np.nan
    return a


def _text_or_float(col, n):
    """Convert a column that may contain text. Numbers stay numbers, text stays text."""
    import pandas as pd

    if col is None:
        return np.empty(0, dtype="float64")

    if col.dtype != object:
        # all rows are numbers
        return _numeric(col, n)

    # The numeric tokens are told apart with Metview's grammar, so inf, nan, Infinity etc. stay
    # text. They are converted with numpy to get the same result as for the other columns.
    text = pd.Series(col, dtype=object)
    is_text = ~text.str.fullmatch(_NUMBER_PATTERN).to_numpy(dtype=bool)
    if not is_text.any():
        return _numeric(text.to_numpy(dtype=object).astype("float64"), n)

    num = np.full(len(col), np.nan, dtype="float64")
    num[~is_text] = text[~is_text].to_numpy(dtype=object).astype("float64")
    num[num == MISSING_VALUE] = np.nan
    out = num.astype(object)
    out[is_text] = text[is_text].to_numpy(dtype=object)
    return out


def _integer_if_possible(a):
    """Truncate to integers; keep float64 only when there are missing values."""
    if np.isfinite(a).all():
        return np.trunc(a).astype("int64")
    return np.trunc(a)


def _decode_stnid(col):
    if col is None:
        return np.empty(0, dtype=object)

    import pandas as pd

    s = pd.Series(col, dtype=object)
    s = s.str.replace("\\32\\", " ", regex=False).str.replace("\\9\\", "\t", regex=False)
    out = s.to_numpy(dtype=object)
    out[out == "?"] = None
    return out


def _make_datetime(date, time):
    """Make datetime64[ns] values from YYYYMMDD dates and HHMM times (both truncated to integers)."""
    import pandas as pd

    n = len(date)
    if n == 0:
        return pd.Series([], dtype="datetime64[ns]").to_numpy()

    d = np.trunc(date)
    valid = np.isfinite(d) & (d > 0) & (d <= 99991231)
    d = np.where(valid, d, 0).astype("int64")

    if time is None:
        t = np.zeros(n, dtype="int64")
    else:
        tt = np.trunc(time)
        valid &= np.isfinite(tt) & (tt >= 0) & (tt <= 2359)
        t = np.where(valid, tt, 0).astype("int64")
    valid &= (t // 100 < 24) & (t % 100 < 60)

    parts = pd.DataFrame({
        "year": d // 10000,
        "month": (d // 100) % 100,
        "day": d % 100,
        "hour": t // 100,
        "minute": t % 100,
    })
    dt = pd.to_datetime(parts, errors="coerce")
    dt = dt.where(valid)
    return dt.astype("datetime64[ns]").to_numpy()
