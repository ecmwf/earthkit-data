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
import re
import sys

import click
from earthkit.cli.main import earthkit
from earthkit.cli.standard_args import (
    SOURCE_HELP,
    TARGET_HELP,
    add_options,
    profile_option,
    source_options,
    split_csv,
    target_options,
)


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
    "--num",
    type=int,
    default=None,
    help="Number of items to list. Positive values list from the front, negative values from the back.",
)
@click.option(
    "--keys",
    multiple=True,
    callback=split_csv,
    help="Metadata keys to show instead of the default set. Comma-separated or repeated.",
)
@click.option(
    "--extra-keys",
    multiple=True,
    callback=split_csv,
    help="Additional metadata keys to show on top of the default set. Comma-separated or repeated.",
)
@click.option(
    "--cubes",
    is_flag=True,
    help="Group items into hypercubes.",
)
def ls(source, num, keys, extra_keys, cubes):
    """List the contents of SOURCE as a metadata summary table.

    --keys replaces the default set of metadata keys shown, --extra-keys adds to it.
    """
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


def _is_stdout(target) -> bool:
    return target.args[1:2] == (sys.stdout.buffer,)


def _check_different_files(source, target) -> None:
    """Raise if the SOURCE and TARGET are the same file on disk.

    No-op when the source or target is not a file, e.g. stdin or stdout.
    """
    path = target.args[1] if len(target.args) > 1 else target.kwargs.get("file")
    if target.args[0] != "file" or not isinstance(path, (str, os.PathLike)) or not os.path.exists(path):
        return
    try:
        source_paths = source.path
    except Exception:
        return
    for source_path in source_paths if isinstance(source_paths, (list, tuple)) else [source_paths]:
        if isinstance(source_path, (str, os.PathLike)) and os.path.exists(source_path):
            if os.path.samefile(source_path, path):
                raise click.ClickException("Source and target files must be different")


def _is_stream(source) -> bool:
    """Return True if SOURCE was read from stdin, which only supports GRIB data."""
    from earthkit.data.data.stream import StreamFieldListData

    return isinstance(source, StreamFieldListData)


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


_DATETIME = r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}(?::\d{2}(?::\d{2}(?:\.\d+)?)?)?)?"
_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_BOUND = rf'"[^"]*"|{_DATETIME}|{_NUMBER}'
_SLICE = re.compile(rf"(?P<start>{_BOUND})?:(?P<stop>{_BOUND})?(?::(?P<step>[-+]?\d+))?")


def _slice_bound(text: str | None) -> str | int | float | datetime.datetime | None:
    """Turn a slice bound into a quoted string, an ISO date-time, an int or a float."""
    if text is None:
        return None
    if text.startswith('"'):
        return text[1:-1]
    if re.fullmatch(_DATETIME, text):
        return datetime.datetime.fromisoformat(text)
    return int(text) if re.fullmatch(r"[-+]?\d+", text) else float(text)


def _selection_item(text: str) -> str | list | slice:
    """Parse a scalar or a START:STOP[:STEP] slice, which includes STOP."""
    text = text.strip()
    if not text:
        raise ValueError("Selection values must not be empty")
    if re.fullmatch(r'"[^"]*"', text):
        return text[1:-1]
    # Scalars stay strings: FieldList.sel casts them to the type of the metadata
    if ":" not in text or re.fullmatch(_DATETIME, text):
        return text
    match = _SLICE.fullmatch(text)
    if match is None:
        raise ValueError("Slices must be START:STOP[:STEP], with numbers, ISO date-times or quoted strings as bounds")
    start, stop = _slice_bound(match["start"]), _slice_bound(match["stop"])
    if start is None and stop is None:
        raise ValueError("Slices need a START or a STOP")
    if start is not None and stop is not None:
        number = (int, float)
        if not (isinstance(start, number) and isinstance(stop, number)) and type(start) is not type(stop):
            raise ValueError("The START and STOP of a slice must have the same type")
    if match["step"] is None:
        return slice(start, stop)
    step = int(match["step"])
    if step == 0 or not (isinstance(start, int) and isinstance(stop, int)):
        raise ValueError("A STEP must not be 0, and needs an integer START and STOP")
    return list(range(start, stop + (1 if step > 0 else -1), step))


def _selection_value(value: str) -> str | list | slice:
    """Parse a scalar, a comma-separated list or a slice for selection.

    Slices include their STOP, as :meth:`~earthkit.data.core.fieldlist.FieldList.sel` and ``xarray.Dataset.sel``
    do. Integer slices in a list, or with a STEP, are expanded to the values they select.
    """
    items = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', value)
    if len(items) == 1:
        return _selection_item(items[0])
    result = []
    for item in items:
        parsed = _selection_item(item)
        if isinstance(parsed, slice):
            if not (isinstance(parsed.start, int) and isinstance(parsed.stop, int)):
                raise ValueError("Only slices with an integer START and STOP can be combined with commas")
            parsed = list(range(parsed.start, parsed.stop + 1))
        result.extend(parsed if isinstance(parsed, list) else [parsed])
    return result


class _SelectionCommand(click.Command):
    """A command taking ``--KEY VALUE`` (or ``--KEY=VALUE``) conditions, for any KEY that is not one of its options.

    The conditions are passed to the command as ``conditions``, a dict of the VALUE strings by KEY.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        takes_value = {
            opt: not (param.is_flag or param.count)
            for param in self.get_params(ctx)
            if isinstance(param, click.Option)
            for opt in param.opts + param.secondary_opts
        }
        rest, conditions = [], {}
        args = iter(args)
        for arg in args:
            if arg == "--":
                rest += [arg, *args]
                break
            name, separator, value = arg.partition("=")
            if not arg.startswith("--") or len(name) == 2 or name in takes_value:
                rest.append(arg)
                # Keep the value of an option of the command, even if it looks like an option
                if takes_value.get(arg):
                    option_value = next(args, None)
                    if option_value is not None:
                        rest.append(option_value)
                continue
            if not separator:
                value = next(args, None)
                if value is None:
                    raise click.UsageError(f"Option {name!r} requires a value.", ctx)
            key = name[2:]
            if key in conditions:
                raise click.UsageError(f"Duplicate selection key {key!r}", ctx)
            conditions[key] = value
        result = super().parse_args(ctx, rest)
        ctx.params["conditions"] = conditions
        return result

    def collect_usage_pieces(self, ctx: click.Context) -> list[str]:
        return [*super().collect_usage_pieces(ctx), "--KEY VALUE [--KEY VALUE]..."]


@earthkit.command(
    cls=_SelectionCommand,
    help=f"""Select GRIB fields, BUFR messages or NetCDF coordinate labels with --KEY VALUE conditions.

\b
VALUE can be:
- a scalar, e.g. --parameter.variable t
- a comma-separated list, e.g. --vertical.level 500,700
- a slice START:STOP[:STEP], which includes STOP, e.g. --vertical.level 300:500 or --vertical.level 700:.
  The bounds are numbers, ISO date-times, e.g. '2020-12-21T00:00:2020-12-22T00:00', or quoted strings,
  e.g. '"a":"c"'. A STEP needs integer bounds, e.g. 300:700:200.

Conditions on different keys are combined with AND. GRIB and BUFR conditions use earthkit-data metadata keys,
NetCDF conditions use coordinate names, e.g. --level 300:500.

SOURCE: {SOURCE_HELP}

TARGET: {TARGET_HELP}

\b
Example:
    earthkit sel input.grib output.grib --parameter.variable t,u --vertical.level 300:500
    cat input.grib | earthkit sel - - --metadata.paramId 131 > output.grib
""",
)
@add_options([source_options(positional=True), target_options(positional=True)])
def sel(source, target, conditions: dict[str, str]) -> None:
    from earthkit.data.data.netcdf import NetCDFData

    if not conditions:
        raise click.UsageError("At least one --KEY VALUE condition is required")
    selection = {}
    for key, value in conditions.items():
        try:
            selection[key] = _selection_value(value)
        except ValueError as error:
            raise click.BadParameter(f"{value!r}: {error}", param_hint=f"'--{key}'") from error

    _check_different_files(source, target)

    try:
        is_netcdf = isinstance(source, NetCDFData)
        if is_netcdf:
            selected = _sel_netcdf(source.to_xarray(), selection)
        else:
            selected = _sel_list(_listable(source, "SOURCE", method="sel", stream=_is_stream(source)), selection)

        if is_netcdf and _is_stdout(target):
            target.to_target(selected, encoder="netcdf")
        else:
            target.to_target(selected)
    except Exception as error:
        raise click.ClickException(f"Could not select: {error}") from error


def _ordered_bounds(value: slice) -> tuple:
    """Return the START and STOP of a slice, swapped if STOP is before START."""
    start, stop = value.start, value.stop
    if start is not None and stop is not None and stop < start:
        return stop, start
    return start, stop


def _sel_list(items, selection):
    """Select from a FieldList or FeatureList, with the slices in SELECTION including their STOP.

    The slices are applied to the metadata values here, since ``sel`` does not support slices for all keys, e.g.
    date-time keys such as ``time.valid_datetime``.
    """
    slices = {key: value for key, value in selection.items() if isinstance(value, slice)}
    others = {key: value for key, value in selection.items() if key not in slices}
    selected = items.sel(others) if others else items
    for key, value in slices.items():
        start, stop = _ordered_bounds(value)

        def included(item_value):
            try:
                return (
                    item_value is not None
                    and (start is None or item_value >= start)
                    and (stop is None or item_value <= stop)
                )
            except TypeError:
                return False

        selected = selected[[i for i, item_value in enumerate(selected.get(key)) if included(item_value)]]
    return selected


def _sel_netcdf(dataset, selection):
    """Select the coordinate labels of DATASET, keeping their order and ignoring absent labels in lists and slices."""
    import numpy as np

    indexers = {}
    for key, value in selection.items():
        coordinate = dataset.coords[key]
        if isinstance(value, slice):
            start, stop = _ordered_bounds(value)
            if coordinate.dtype.kind == "M":
                start, stop = (None if v is None else np.datetime64(v) for v in (start, stop))
            mask = np.ones(coordinate.shape, dtype=bool)
            if start is not None:
                mask &= (coordinate >= start).values
            if stop is not None:
                mask &= (coordinate <= stop).values
            indexers[key] = coordinate[mask]
        elif isinstance(value, list):
            indexers[key] = coordinate[coordinate.isin(np.asarray(value, dtype=coordinate.dtype))]
        else:
            indexers[key] = coordinate.dtype.type(value)
    return dataset.sel(indexers)


def _ordering(ctx: click.Context, param: click.Parameter, keys: tuple[str, ...]) -> dict[str, str | list[str]]:
    """Turn the KEY[=ORDER] values of --key into the ordering of :meth:`FieldList.order_by`."""
    ordering = {}
    for argument in keys:
        key, separator, value = argument.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            raise click.BadParameter("Ordering keys must not be empty")
        if key in ordering:
            raise click.BadParameter(f"Duplicate ordering key {key!r}")
        if not separator:
            ordering[key] = "ascending"
        elif value in ("ascending", "descending"):
            ordering[key] = value
        elif "," in value:
            values = [item.strip() for item in value.split(",")]
            if any(not item for item in values) or len(values) != len(set(values)):
                raise click.BadParameter("Custom order values must be non-empty and unique")
            ordering[key] = values
        else:
            raise click.BadParameter(
                f"Expected KEY, KEY=ascending, KEY=descending or KEY=value1,value2, got {argument!r}"
            )
    return ordering


@earthkit.command(
    name="order_by",
    help=f"""Order GRIB fields or BUFR messages by metadata keys.

Give each key with --key, in the order they are applied. A bare KEY uses ascending order. Use KEY=ascending or
KEY=descending to specify the direction, or KEY=value1,value2 for a custom order containing all values.

SOURCE: {SOURCE_HELP}

TARGET: {TARGET_HELP}

\b
Example:
    earthkit order_by input.grib output.grib --key vertical.level=descending --key parameter.variable
    cat input.grib | earthkit order_by - - --key parameter.variable=v,u,t > output.grib
""",
)
@add_options([source_options(positional=True), target_options(positional=True)])
@click.option(
    "--key",
    "ordering",
    multiple=True,
    required=True,
    callback=_ordering,
    metavar="KEY[=ORDER]",
    help="Key to order by, as KEY, KEY=ascending, KEY=descending or KEY=value1,value2. Can be repeated.",
)
def order_by(source, target, ordering: dict[str, str | list[str]]) -> None:
    from earthkit.data.data.bufr import BUFRData
    from earthkit.data.data.grib import GribData

    _check_different_files(source, target)

    stream = _is_stream(source)
    if not stream and not isinstance(source, (GribData, BUFRData)):
        raise click.ClickException("'order_by' only supports GRIB and BUFR input")
    try:
        target.to_target(_listable(source, "SOURCE", method="order_by", stream=stream).order_by(ordering))
    except Exception as error:
        raise click.ClickException(f"Could not order: {error}") from error
