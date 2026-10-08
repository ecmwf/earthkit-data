# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Commands contributed by earthkit-data to the shared ``earthkit`` command line interface.

The ``earthkit`` console script itself lives in :mod:`earthkit.cli.main` (earthkit-utils). This module is
part of the ``earthkit.cli`` namespace package, which is shared by all earthkit packages, and registers its commands on
the shared ``earthkit`` group with ``@earthkit.command()``, so ``earthkit ls <file>`` becomes available once
earthkit-data is installed.

This module lives outside of ``earthkit.data`` on purpose, so that listing the commands does not import
``earthkit.data``. Only import :mod:`click` and light standard library modules at module level, and import
everything else inside the command functions.
"""

import datetime
import os
import sys
from collections.abc import Callable

import click
from earthkit.cli.main import earthkit
from earthkit.cli.standard_args import add_options, profile_option, source_options, target_options


def _split_csv(ctx, param, value):
    """Turn a tuple of (possibly comma-separated) option values into a flat list."""
    if not value:
        return None
    result = []
    for item in value:
        result.extend(v.strip() for v in item.split(",") if v.strip())
    return result or None


def _ls_cubes(df):
    def _walk(node, cols):
        if not cols:
            return [{"__num__": len(node)}]
        col = cols[0]
        cubes = []
        groups = []
        na = node[col].isna()
        if na.any():
            groups.append((None, node[na]))
        groups.extend(node.groupby(col))
        for val, child in groups:
            for sub in _walk(child, cols[1:]):
                for vals, cube in cubes:
                    if sub == cube:
                        vals.append(val)
                        break
                else:
                    cubes.append(([val], sub))
        return [{col: vals, **cube} for vals, cube in cubes]

    first = True
    for cube in _walk(df, list(df.columns)):
        w = 0
        num = 0
        lines = []
        for key, vals in cube.items():
            if key == "__num__":
                num = vals
                continue
            w = max(w, len(key))
            vals_s = ("[" + ", ".join(str(val) for val in vals) + "]") if len(vals) != 1 else str(vals[0])
            lines.append((key, vals_s))
        if w == 0:
            continue
        if first:
            first = False
        else:
            click.echo()
        if num > 1:
            click.echo(" " * w + f"  ({num} items)")
        for key, vals in lines:
            click.echo(f"{key:<{w}s}  {vals}")


@earthkit.command()
@add_options([source_options(positional=True)])
@click.option(
    "-n",
    "--num",
    type=int,
    default=None,
    help="Number of items to list. Positive values list from the front, negative values from the back.",
)
@click.option(
    "-k",
    "--keys",
    multiple=True,
    callback=_split_csv,
    help="Metadata keys to show instead of the default set. Comma-separated or repeated.",
)
@click.option(
    "-e",
    "--extra-keys",
    multiple=True,
    callback=_split_csv,
    help="Additional metadata keys to show on top of the default set. Comma-separated or repeated.",
)
@click.option(
    "--cubes",
    is_flag=True,
    help="Group items into hypercubes.",
)
def ls(source, num, keys, extra_keys, cubes):
    """List the contents of FILENAME as a metadata summary table."""
    import pandas as pd

    ds = _listable(source, None)

    kwargs = {}
    if num is not None:
        kwargs["n"] = num
    if keys is not None:
        kwargs["keys"] = keys
    if extra_keys is not None:
        kwargs["extra_keys"] = extra_keys

    df = ds.ls(**kwargs)
    if df is None:
        return

    if cubes:
        _ls_cubes(df)
        return

    with pd.option_context(
        "display.max_rows",
        None,
        "display.max_columns",
        None,
        "display.width",
        None,
        "display.max_colwidth",
        None,
    ):
        click.echo(df.to_string())


def _check_different_files(source_file: str, target_file: str) -> None:
    """Raise if SOURCE_FILE and TARGET_FILE are the same file on disk.

    No-op when either side is ``-`` (stdin/stdout), since there is then no real file to compare.
    """
    if source_file == "-" or target_file == "-":
        return
    if os.path.exists(target_file) and os.path.samefile(source_file, target_file):
        raise click.ClickException("Source and target files must be different")


def _read_source(source_file: str):
    """Read SOURCE_FILE, or GRIB data from stdin when SOURCE_FILE is ``-``.

    Returns
    -------
    tuple
        ``(data, stream)`` where ``data`` is the loaded :class:`~earthkit.data.data.Data` object
        and ``stream`` is True when it was read from stdin. Downstream code should pass
        ``stream`` to :func:`_listable` so field/feature lists get materialised with
        ``read_all=True``, since a single-pass stream cannot support random access operations
        such as ``sel`` or ``order_by``.

    Raises
    ------
    click.ClickException
        If SOURCE_FILE is ``-`` and the stdin data is not GRIB, since that is the only format
        that currently supports being read from a stream.
    """
    from earthkit.data import from_source
    from earthkit.data.data.stream import StreamFieldListData

    if source_file == "-":
        data = from_source("stream", sys.stdin.buffer)
        if not isinstance(data, StreamFieldListData):
            raise click.ClickException("Reading from stdin is only supported for GRIB input")
        return data, True

    return from_source("file", source_file), False


def _write_target(target_file: str, data, **kwargs) -> None:
    """Write DATA to TARGET_FILE, or to stdout when TARGET_FILE is ``-``."""
    from earthkit.data import to_target

    if target_file == "-":
        to_target("file", sys.stdout.buffer, data=data, **kwargs)
    else:
        to_target("file", target_file, data=data, **kwargs)


def _listable(ds, filename, method="ls", stream=False):
    """Return an object with the requested method for data loaded from ``filename``.

    :func:`from_source` returns a :class:`~earthkit.data.data.Data` object. Depending on the
    file format it can be converted into a FieldList (e.g. GRIB, NetCDF) or a FeatureList
    (e.g. BUFR), both of which provide ``ls`` and ``sel``.
    """
    if hasattr(ds, method):
        return ds

    available = getattr(ds, "available_types", None) or []
    for type_name in ("fieldlist", "featurelist"):
        if type_name in available:
            try:
                if not stream:
                    obj = ds.to(type_name)
                else:
                    obj = ds.to(type_name, read_all=True)
            except Exception as e:
                raise click.ClickException(f"Could not convert {filename!r} to a {type_name}: {e}")
            if hasattr(obj, method):
                return obj

    raise click.ClickException(f"{method!r} is not supported for {filename!r} ({type(ds).__name__})")


@earthkit.command()
@add_options([source_options(positional=True), target_options(positional=True), profile_option])
def convert(source, target, profile):
    """Convert a data file to xarray format using the specified profile(s)."""
    out_data = source.to_xarray(profile=profile)
    target.to_target(data=out_data)


def _selection_value(value: str) -> str | list | Callable:
    """Parse a scalar, comma-separated list or integer range for selection."""
    if "," in value:
        items = value.split(",")
        if any(not item.strip() for item in items):
            raise ValueError("List values must not be empty")
        result = []
        for item in items:
            parsed = _selection_value(item.strip())
            if callable(parsed):
                raise ValueError("Open-ended slices cannot be combined with comma-separated values")
            result.extend(parsed if isinstance(parsed, list) else [parsed])
        return result
    if ":" in value:
        try:
            datetime.datetime.fromisoformat(value.strip())
        except ValueError:
            pass
        else:
            return value.strip()
        parts = value.split(":")
        if len(parts) == 2 and bool(parts[0].strip()) != bool(parts[1].strip()):
            if not parts[0].strip():
                stop = int(parts[1])
                return lambda number: number is not None and number < stop
            start = int(parts[0])
            return lambda number: number is not None and number >= start
        if len(parts) not in (2, 3) or any(not part.strip() for part in parts):
            raise ValueError("Slices must be START:STOP[:STEP], :STOP or START: with integer bounds")
        return list(range(*(int(part) for part in parts)))
    if not value.strip():
        raise ValueError("Selection values must not be empty")
    return value.strip()


@earthkit.command()
@click.argument("source-file", type=click.Path(exists=True, dir_okay=False, allow_dash=True))
@click.argument("target-file", type=click.Path(dir_okay=False))
@click.argument("conditions", nargs=-1, required=True)
def sel(source_file: str, target_file: str, conditions: tuple[str, ...]) -> None:
    """Select fields or BUFR messages using KEY=VALUE conditions.

    Values can be comma-separated lists or integer slices with an exclusive stop.
    For example: earthkit sel input.grib output.grib metadata.level=1:4
    NetCDF conditions use native xarray coordinate names, for example level=300:500.
    Use '-' as SOURCE_FILE to read GRIB data from stdin (not currently supported for BUFR or NetCDF).
    Use '-' as TARGET_FILE to write the result to stdout.
    """
    from earthkit.data.data.netcdf import NetCDFData

    selection = {}
    for condition in conditions:
        key, separator, value = condition.partition("=")
        key = key.strip()
        if not separator or not key:
            raise click.BadParameter(f"Expected KEY=VALUE, got {condition!r}", param_hint="conditions")
        if key in selection:
            raise click.BadParameter(f"Duplicate selection key {key!r}", param_hint="conditions")
        try:
            selection[key] = _selection_value(value)
        except ValueError as error:
            raise click.BadParameter(f"Invalid selection {condition!r}: {error}", param_hint="conditions") from error

    to_stdout = target_file == "-"
    _check_different_files(source_file, target_file)

    try:
        data, stream = _read_source(source_file)

        is_netcdf = isinstance(data, NetCDFData)
        if is_netcdf:
            dataset = data.to_xarray()
            indexers = {}
            for key, value in selection.items():
                coordinate = dataset.coords[key]
                if callable(value):
                    indexers[key] = coordinate[[value(number) for number in coordinate.values]]
                elif isinstance(value, list):
                    import numpy as np

                    values = np.asarray(value, dtype=coordinate.dtype)
                    indexers[key] = coordinate[coordinate.isin(values)]
                else:
                    indexers[key] = coordinate.dtype.type(value)
            selected = dataset.sel(indexers)
        else:
            data = _listable(data, source_file, method="sel", stream=stream)
            selected = data.sel(selection)

        if is_netcdf and to_stdout:
            _write_target(target_file, selected, encoder="netcdf")
        else:
            _write_target(target_file, selected)
    except Exception as error:
        raise click.ClickException(f"Could not select from {source_file!r}: {error}") from error


@earthkit.command(name="order_by")
@click.argument("source-file", type=click.Path(exists=True, dir_okay=False, allow_dash=True))
@click.argument("target-file", type=click.Path(dir_okay=False))
@click.argument("keys", nargs=-1, required=True)
def order_by(source_file: str, target_file: str, keys: tuple[str, ...]) -> None:
    """Order GRIB fields or BUFR messages by metadata keys.

    Bare keys use ascending order. Use KEY=ascending or KEY=descending to specify
    direction, or KEY=value1,value2 to specify a custom order containing all values.
    Keys are applied in the order given.
    Use '-' as SOURCE_FILE to read GRIB data from stdin (not currently supported for BUFR).
    Use '-' as TARGET_FILE to write the result to stdout.
    """
    from earthkit.data.data.bufr import BUFRData
    from earthkit.data.data.grib import GribData

    ordering = {}
    for argument in keys:
        key, separator, value = argument.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            raise click.BadParameter("Ordering keys must not be empty", param_hint="keys")
        if key in ordering:
            raise click.BadParameter(f"Duplicate ordering key {key!r}", param_hint="keys")
        if not separator:
            ordering[key] = "ascending"
        elif value in ("ascending", "descending"):
            ordering[key] = value
        elif "," in value:
            values = [item.strip() for item in value.split(",")]
            if any(not item for item in values) or len(values) != len(set(values)):
                raise click.BadParameter("Custom order values must be non-empty and unique", param_hint="keys")
            ordering[key] = values
        else:
            raise click.BadParameter(
                f"Expected KEY, KEY=ascending, KEY=descending or KEY=value1,value2, got {argument!r}",
                param_hint="keys",
            )

    _check_different_files(source_file, target_file)

    try:
        data, stream = _read_source(source_file)
        if not stream and not isinstance(data, (GribData, BUFRData)):
            raise click.ClickException("'order_by' only supports GRIB and BUFR input")

        data = _listable(data, source_file, method="order_by", stream=stream)
        ordered = data.order_by(ordering)
        _write_target(target_file, ordered)
    except click.ClickException:
        raise
    except Exception as error:
        raise click.ClickException(f"Could not order {source_file!r}: {error}") from error
