# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""FieldList for geopoints data.

Each geopoints block is turned into point fields: one field per value column (``value`` for the
traditional and XYV formats, ``x-comp`` and ``y-comp`` for XY_VECTOR, ``magnitude`` and ``angle`` for
POLAR_VECTOR, every non-coordinate column for NCOLS). The values, latitudes and longitudes of a field
are the rows of the block, or in "group" mode the rows of a group of the block. The time and the level
are taken from the first row of the block or group (or from ``#METADATA``, see :func:`make_fieldlist`)
and the ``#METADATA`` pairs are the labels of the fields.
"""

import datetime
import hashlib
import logging
import warnings

import numpy as np

from earthkit.data.field.component.geography import LatLonGeography
from earthkit.data.field.component.level_type import LevelTypes

LOG = logging.getLogger(__name__)

#: The modes accepted by ``to_fieldlist()``.
FIELDLIST_MODES = ("block", "group")

#: Columns of an NCOLS block that are not value columns.
_NCOLS_COORDINATES = ("stnid", "latitude", "longitude", "level", "elevation", "date", "time")

#: The value columns of the fixed formats.
_FIXED_VALUE_COLUMNS = {
    "TRADITIONAL": ["value"],
    "XYV": ["value"],
    "XY_VECTOR": ["x-comp", "y-comp"],
    "POLAR_VECTOR": ["magnitude", "angle"],
}

#: ``#METADATA`` keys holding the parameter name, the units and the level type, in order of preference.
_PARAM_KEYS = ("param", "shortName")
_LEVEL_TYPE_KEYS = ("levtype", "level_type", "typeOfLevel")

#: MARS level types (as written in ``levtype``) and the matching earthkit level type names. Other
#: values are passed on as they are.
_MARS_LEVEL_TYPES = {
    "pl": LevelTypes.PRESSURE.value.name,
    "ml": LevelTypes.HYBRID.value.name,
    "pt": LevelTypes.THETA.value.name,
    "pv": LevelTypes.PV.value.name,
    "sfc": LevelTypes.SURFACE.value.name,
    "sol": LevelTypes.SNOW.value.name,
}


def check_mode(mode, group_by=None):
    """Raise ValueError when the arguments of ``to_fieldlist()`` are not valid.

    The error is raised when ``mode`` is not one of :data:`FIELDLIST_MODES` and when ``group_by`` is
    given for a mode other than "group".
    """
    if not isinstance(mode, str) or mode not in FIELDLIST_MODES:
        allowed = ", ".join(repr(m) for m in FIELDLIST_MODES)
        raise ValueError(f"Invalid fieldlist mode={mode!r}. Allowed modes: {allowed}")

    if group_by is not None and mode != "group":
        raise ValueError(f"group_by can only be used with mode='group', not with mode={mode!r}")


def make_fieldlist(items, mode="block", group_by=None):
    """Build the fieldlist for the parsed geopoints blocks ``items`` in the given ``mode``.

    Parameters
    ----------
    items: list of tuple
        ``(path, block)`` pairs, in order. ``block`` is a
        :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`; ``path`` is the file it
        comes from and is only used in error and warning messages.
    mode: str
        - "block": one field per block and value column.
        - "group": each block is split into groups of rows that share the same values in the
          ``group_by`` columns, one field per group and value column.
    group_by: list of str, optional
        The columns whose values define the groups in "group" mode. Any column of the block can be
        used (e.g. ``stnid``, ``elevation``). The default is the ``date`` and ``level`` columns of
        the block, those that exist. A single name is the same as a list with one name. With no
        columns (an empty list, or a block without ``date`` and ``level`` columns) the whole block is
        one group. Not allowed in "block" mode.

    Returns
    -------
    :class:`~earthkit.data.indexing.simple.SimpleFieldList`
        The fields of the blocks in order: block first, then (in "group" mode) group in order of
        first appearance in the block, then value column in the order of the columns of the block.
        Blocks without rows and non-numeric value columns give no field.

    Raises
    ------
    ValueError
        For an invalid ``mode`` or a ``group_by`` with ``mode="block"``, for a ``group_by`` column
        the block does not have (the message names the column and the file), and for a
        ``#METADATA`` ``step``, ``date``, ``time`` or ``level`` that cannot be used (the message
        names the file).

    Notes
    -----
    The time of a field is the date/time of the first row of the block or, in "group" mode, of the
    group (the ``date`` column holds the validity date and time). When ``#METADATA`` has a ``step``,
    the base time is the validity time minus the step, otherwise the step is 0 and the base time is
    the validity time. A block without ``date`` column uses the ``#METADATA`` pairs ``date``
    (YYYYMMDD) and ``time`` (HHMM) if they are present. The level is the ``level`` of the first row
    (of the group), or the ``#METADATA`` ``level``.

    In "group" mode the rows with a missing key value (NaT or NaN) form a group of their own (for
    each combination of the other keys); if the first row of a group has no date (or level) its
    fields have no time (or level). The labels of a field are the ``#METADATA`` pairs plus the values of the group keys
    other than ``date`` and ``level`` (e.g. ``stnid``), which win on a name clash.
    """
    from earthkit.data.indexing.simple import SimpleFieldList

    check_mode(mode, group_by)
    group_by = _normalise_group_by(group_by)

    fields = []
    for path, block in items:
        if mode == "group":
            fields.extend(_block_group_fields(path, block, group_by))
        else:
            fields.extend(_block_fields(path, block))
    return SimpleFieldList(fields)


# -- geography -----------------------------------------------------------------------------------


class GeopointsGeography(LatLonGeography):
    """The geography of a point field: the latitudes and longitudes of the points, in a 1-D array.

    The shape is always ``(n,)``, also for 0 or 1 points. Unlike its base class, the
    :meth:`unique_grid_id` depends on the coordinates, so that two fields with different points
    never share a grid.
    """

    def __init__(self, latitudes, longitudes):
        lat = np.array(latitudes, dtype="float64")
        lon = np.array(longitudes, dtype="float64")
        super().__init__(lat, lon, shape=lat.shape)
        self._grid_id = None

    def unique_grid_id(self):
        if self._grid_id is None:
            h = hashlib.sha1()
            h.update(np.ascontiguousarray(self._lat, dtype="float64").tobytes())
            h.update(np.ascontiguousarray(self._lon, dtype="float64").tobytes())
            self._grid_id = f"geopoints-{len(self._lat)}-{h.hexdigest()}"
        return self._grid_id


# -- what is shared by the fields of one block ---------------------------------------------------


class _BlockInfo:
    """What the fields built from the rows of one block have in common.

    Parameters
    ----------
    path: str
        The file of the block, used in messages.
    block: :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`
        The block.
    """

    def __init__(self, path, block):
        self.path = path
        self.metadata = dict(block.metadata)
        frame = block._frame

        names = _value_columns(block)
        self.value_columns = []
        for name in names:
            if frame[name].dtype.kind in "fiub" or len(frame) == 0:
                self.value_columns.append(name)
            else:
                warnings.warn(
                    f"{path}: the column {name!r} is not numeric, no field is created for it",
                    UserWarning,
                    stacklevel=2,
                )

        param = None
        if len(names) == 1:
            for k in _PARAM_KEYS:
                if k in self.metadata:
                    param = str(self.metadata[k])
                    break
        self._single_param = param
        self.single_column = len(names) == 1

        units = self.metadata.get("units")
        self.units = None if units is None else str(units)

        self.level_type = None
        for k in _LEVEL_TYPE_KEYS:
            if k in self.metadata:
                t = str(self.metadata[k])
                self.level_type = _MARS_LEVEL_TYPES.get(t, t)
                break

        # the step is the same for all the fields of the block
        self.step = _get_step(path, self.metadata)

        # time and level of rows without own values: from #METADATA
        self.metadata_datetime = None
        self.metadata_level = None
        self._has_date = "date" in frame.columns
        self._has_level = "level" in frame.columns
        if not self._has_date:
            self.metadata_datetime = _get_metadata_datetime(path, self.metadata)
        if not self._has_level:
            self.metadata_level = _get_metadata_level(path, self.metadata)

    def variable(self, column):
        if self._single_param is not None:
            return self._single_param
        return column


def _value_columns(block):
    if block.format in _FIXED_VALUE_COLUMNS:
        return list(_FIXED_VALUE_COLUMNS[block.format])
    return [c for c in block._frame.columns if c not in _NCOLS_COORDINATES]


def _block_fields(path, block):
    """Return the list of fields of a block."""
    if len(block) == 0:
        return []

    info = _BlockInfo(path, block)
    return _make_fields(info, block._frame)


def _normalise_group_by(group_by):
    """Return ``group_by`` as a list of unique column names, or None."""
    if group_by is None:
        return None
    if isinstance(group_by, str):
        group_by = [group_by]
    else:
        try:
            group_by = list(group_by)
        except TypeError:
            raise ValueError(f"group_by must be a list of column names, got {group_by!r}") from None

    for c in group_by:
        if not isinstance(c, str):
            raise ValueError(f"group_by must be a list of column names, got {c!r}")
    return list(dict.fromkeys(group_by))


def _block_group_fields(path, block, group_by):
    """Return the list of fields of a block split into groups of rows."""
    if len(block) == 0:
        return []

    frame = block._frame
    if group_by is None:
        keys = [c for c in ("date", "level") if c in frame.columns]
    else:
        keys = group_by
        for c in keys:
            if c not in frame.columns:
                raise ValueError(
                    f"{path}: cannot group by the column {c!r}, the block has the columns "
                    f"{', '.join(repr(x) for x in frame.columns)}"
                )

    info = _BlockInfo(path, block)

    # no grouping columns: the whole block is one group
    if not keys:
        return _make_fields(info, frame)

    # The group number of each row. With sort=False the numbers follow the first appearance of
    # the groups, and with dropna=False the rows with NaT/NaN keys are a group, too.
    codes = frame.groupby(keys, sort=False, dropna=False).ngroup().to_numpy()
    n_groups = int(codes.max()) + 1
    if n_groups == 1:
        return _make_fields(info, frame, labels=_key_labels(frame.iloc[0], keys))

    # positions of the rows of each group, in the order of the block
    order = np.argsort(codes, kind="stable")
    ends = np.cumsum(np.bincount(codes, minlength=n_groups))
    starts = ends - np.bincount(codes, minlength=n_groups)

    fields = []
    for start, end in zip(starts, ends):
        sub = frame.iloc[order[start:end]]
        fields.extend(_make_fields(info, sub, labels=_key_labels(sub.iloc[0], keys)))
    return fields


def _key_labels(first, keys):
    """Return the labels from the group keys other than ``date`` and ``level``.

    ``first`` is the first row of the group. Missing values give no label.
    """
    import pandas as pd

    labels = {}
    for k in keys:
        if k in ("date", "level"):
            continue
        v = first[k]
        if pd.isna(v):
            continue
        if isinstance(v, pd.Timestamp):
            v = v.to_pydatetime()
        elif isinstance(v, np.generic):
            v = v.item()
        labels[k] = v
    return labels


def _make_fields(info, frame, labels=None):
    """Return the fields for the rows ``frame`` of a block, one for each value column.

    The time and the level are taken from the first row of ``frame``. ``frame`` must have rows.

    Parameters
    ----------
    info: :class:`_BlockInfo`
        The properties of the block the rows belong to.
    frame: :py:class:`pandas.DataFrame`
        The rows (a block or a part of it).
    labels: dict, optional
        Labels added to the ``#METADATA`` pairs of the block; they win on a name clash.
    """
    from earthkit.data.core.field import Field

    if len(frame) == 0 or not info.value_columns:
        return []

    first = frame.iloc[0]
    time = _make_time(info, first)
    vertical = _make_vertical(info, first)

    lat = frame["latitude"].to_numpy(dtype="float64")
    lon = frame["longitude"].to_numpy(dtype="float64")

    all_labels = dict(info.metadata)
    if labels:
        all_labels.update(labels)

    fields = []
    for column in info.value_columns:
        parameter = {"variable": info.variable(column)}
        if info.units is not None:
            parameter["units"] = info.units

        fields.append(
            Field.from_components(
                values=np.array(frame[column], dtype="float64"),
                parameter=parameter,
                time=time,
                vertical=vertical,
                geography=GeopointsGeography(lat, lon),
                labels=dict(all_labels),
            )
        )
    return fields


# -- time, level ---------------------------------------------------------------------------------


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _get_step(path, metadata):
    """Return the ``step`` of the ``#METADATA`` as a timedelta, or None."""
    if "step" not in metadata:
        return None

    step = metadata["step"]
    try:
        if _is_number(step):
            return datetime.timedelta(hours=step)
        if isinstance(step, str):
            from earthkit.data.utils.dates import to_timedelta

            td = to_timedelta(step)
            if td is not None:
                return td
    except (ValueError, TypeError, OverflowError):
        pass

    raise ValueError(f"{path}: cannot use #METADATA step={step!r} as a step (a number of hours or e.g. '6h')")


def _get_metadata_datetime(path, metadata):
    """Return the datetime made of the ``#METADATA`` ``date`` (YYYYMMDD) and ``time`` (HHMM), or None."""
    date = metadata.get("date")
    if date is None:
        return None

    time = metadata.get("time", 0)
    try:
        if not _is_number(date) or not _is_number(time) or date != int(date) or time != int(time):
            raise ValueError
        date = int(date)
        time = int(time)
        return datetime.datetime(date // 10000, (date // 100) % 100, date % 100, time // 100, time % 100)
    except (ValueError, OverflowError):
        raise ValueError(
            f"{path}: cannot use #METADATA date={date!r} time={metadata.get('time')!r} as a date "
            "(YYYYMMDD) and a time (HHMM)"
        ) from None


def _get_metadata_level(path, metadata):
    """Return the ``#METADATA`` ``level`` as a Python number, or None."""
    if "level" not in metadata:
        return None

    level = metadata["level"]
    if not _is_number(level):
        raise ValueError(f"{path}: cannot use #METADATA level={level!r} as a level (a number)")
    return _number(level)


def _number(x):
    """Return the Python int for an integral number, else a Python float. None for NaN and infinity."""
    x = float(x)
    if not np.isfinite(x):
        return None
    return int(x) if x.is_integer() else x


def _make_time(info, row):
    """Return the time dict for the first row of a block or group, or None when there is no time."""
    import pandas as pd

    if info._has_date:
        date = row["date"]
        if pd.isna(date):
            return None
        valid = pd.Timestamp(date).to_pydatetime()
    else:
        valid = info.metadata_datetime
        if valid is None:
            return None

    if info.step is None:
        return {"valid_datetime": valid}
    return {"valid_datetime": valid, "step": info.step}


def _make_vertical(info, row):
    """Return the vertical dict for the first row of a block or group, or None."""
    if info._has_level:
        level = _number(row["level"])
    else:
        level = info.metadata_level

    d = {}
    if level is not None:
        d["level"] = level
    if info.level_type is not None:
        d["level_type"] = info.level_type
    return d or None
