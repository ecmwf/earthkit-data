# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""Commands contributed by earthkit-data to the shared ``earthkit`` command line interface.

The ``earthkit`` console script itself lives in :mod:`earthkit.utils.cli`. The commands
defined here are registered with it through the ``earthkit.cli`` entry point group in
``pyproject.toml``, so ``earthkit ls <file>`` becomes available once earthkit-data is installed.
"""

import datetime
import os
from collections.abc import Callable

import click


def _split_csv(ctx, param, value):
    """Turn a tuple of (possibly comma-separated) option values into a flat list."""
    if not value:
        return None
    result = []
    for item in value:
        result.extend(v.strip() for v in item.split(",") if v.strip())
    return result or None


@click.command()
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
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
def ls(filename, num, keys, extra_keys):
    """List the contents of FILENAME as a metadata summary table."""
    import pandas as pd

    from earthkit.data import from_source

    ds = _listable(from_source("file", filename), filename)

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


def _listable(ds, filename, method="ls"):
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
                obj = ds.to(type_name)
            except Exception as e:
                raise click.ClickException(f"Could not convert {filename!r} to a {type_name}: {e}")
            if hasattr(obj, method):
                return obj

    raise click.ClickException(f"{method!r} is not supported for {filename!r} ({type(ds).__name__})")


@click.command()
@click.argument("source-file", type=click.Path(exists=True, dir_okay=False))
@click.argument("target-file", type=click.Path(exists=False, dir_okay=False))
@click.option(
    "--profile",
    type=str,
    default="earthkit",
    help="Name of the xr-engine profile to use for conversion ('earthkit', 'grib', 'mars', 'defaults')",
)
@click.option(
    "--profile-file",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="YAML or JSON file containing a custom xr-engine profile",
)
def convert(source_file, target_file, profile, profile_file):
    """Convert a data file to xarray format using the specified profile."""
    import earthkit.data as ekd

    in_data = ekd.from_source("file", source_file)
    if profile_file:
        from earthkit.data.xr_engine.profile import Profile

        custom_profile = _read_profile(profile_file)
        profile = Profile.make(profile, **custom_profile)

    out_data = in_data.to_xarray(profile=profile)  # profile is of the Profile type, which is accepted by to_xarray
    # but not documented in the public API. It is used internally to control the conversion process.

    ekd.to_target("file", target_file, data=out_data)


def _read_profile(filename):
    """Read a YAML profile file and return its contents as a dictionary."""
    import yaml

    with open(filename, "r") as f:
        try:
            profile = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise click.ClickException(f"Error reading profile file {filename!r}: {e}")
    if not isinstance(profile, dict):
        raise click.ClickException(f"Profile file {filename!r} does not contain a valid dictionary")
    return profile


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


@click.command()
@click.argument("source-file", type=click.Path(exists=True, dir_okay=False))
@click.argument("target-file", type=click.Path(dir_okay=False))
@click.argument("conditions", nargs=-1, required=True)
def sel(source_file: str, target_file: str, conditions: tuple[str, ...]) -> None:
    """Select fields or BUFR messages using KEY=VALUE conditions.

    Values can be comma-separated lists or integer slices with an exclusive stop.
    For example: earthkit sel input.grib output.grib metadata.level=1:4
    NetCDF conditions use native xarray coordinate names, for example level=300:500.
    """
    from earthkit.data import from_source, to_target
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

    if os.path.exists(target_file) and os.path.samefile(source_file, target_file):
        raise click.ClickException("Source and target files must be different")

    try:
        data = from_source("file", source_file)
        if isinstance(data, NetCDFData):
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
            data = _listable(data, source_file, method="sel")
            selected = data.sel(selection)
        to_target("file", target_file, data=selected)
    except Exception as error:
        raise click.ClickException(f"Could not select from {source_file!r}: {error}") from error


@click.command(name="order_by")
@click.argument("source-file", type=click.Path(exists=True, dir_okay=False))
@click.argument("target-file", type=click.Path(dir_okay=False))
@click.argument("keys", nargs=-1, required=True)
def order_by(source_file: str, target_file: str, keys: tuple[str, ...]) -> None:
    """Order GRIB fields or BUFR messages by metadata keys.

    Bare keys use ascending order. Use KEY=ascending or KEY=descending to specify
    direction, or KEY=value1,value2 to specify a custom order containing all values.
    Keys are applied in the order given.
    """
    from earthkit.data import from_source, to_target
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

    if os.path.exists(target_file) and os.path.samefile(source_file, target_file):
        raise click.ClickException("Source and target files must be different")

    try:
        data = from_source("file", source_file)
        if not isinstance(data, (GribData, BUFRData)):
            raise click.ClickException("'order_by' only supports GRIB and BUFR input")
        data = _listable(data, source_file, method="order_by")
        ordered = data.order_by(ordering)
        to_target("file", target_file, data=ordered)
    except click.ClickException:
        raise
    except Exception as error:
        raise click.ClickException(f"Could not order {source_file!r}: {error}") from error


COMMANDS = {
    "ls": ls,
    "convert": convert,
    "sel": sel,
    "order_by": order_by,
}
