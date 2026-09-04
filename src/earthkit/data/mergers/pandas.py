# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def merge(
    sources=None,
    paths=None,
    reader_class=None,
    **kwargs,
):
    """Merge ``sources`` into a single pandas DataFrame.

    Each source is converted with ``to_pandas()`` and the results are concatenated with
    ``pandas.concat``.

    Parameters
    ----------
    sources : list of :class:`earthkit.data.sources.Source`, optional
        The sources to merge.
    paths : list of str, optional
        Unused.
    reader_class : type, optional
        Unused.
    **kwargs
        Additional keyword arguments. ``pandas_read_csv_kwargs``, if present, is forwarded as-is to each
        source's ``to_pandas()`` call instead of being merged into the ``pandas.concat`` options; otherwise
        all of ``kwargs`` is forwarded for that purpose. Any other keys are passed to ``pandas.concat``,
        overriding the default ``ignore_index=True``.

    Returns
    -------
    pandas.DataFrame
    """
    import pandas as pd

    options = dict(ignore_index=True)  # Renumber all indices
    options.update(kwargs)
    if "pandas_read_csv_kwargs" in options:
        pandas_read_csv_kwargs = options.pop("pandas_read_csv_kwargs")
    else:
        pandas_read_csv_kwargs = kwargs
    return pd.concat([s.to_pandas(pandas_read_csv_kwargs=pandas_read_csv_kwargs) for s in sources], **options)
