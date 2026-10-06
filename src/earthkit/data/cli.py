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
