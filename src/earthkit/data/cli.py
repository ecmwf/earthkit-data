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


def _listable(ds, filename):
    """Return an object with an ``ls`` method for the data loaded from ``filename``.

    :func:`from_source` returns a :class:`~earthkit.data.data.Data` object. Depending on the
    file format it can be converted into a FieldList (e.g. GRIB, NetCDF) or a FeatureList
    (e.g. BUFR), both of which provide ``ls``.
    """
    if hasattr(ds, "ls"):
        return ds

    available = getattr(ds, "available_types", None) or []
    for type_name in ("fieldlist", "featurelist"):
        if type_name in available:
            try:
                obj = ds.to(type_name)
            except Exception as e:
                raise click.ClickException(f"Could not convert {filename!r} to a {type_name}: {e}")
            if hasattr(obj, "ls"):
                return obj

    raise click.ClickException(f"'ls' is not supported for {filename!r} ({type(ds).__name__})")


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


COMMANDS = {
    "ls": ls,
    "convert": convert,
}
