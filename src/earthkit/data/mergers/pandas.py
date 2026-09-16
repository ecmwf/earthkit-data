# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def merge(
    items=None,
    paths=None,
    reader_class=None,
    **kwargs,
):
    """Merge ``items`` into a single pandas DataFrame.

    Each item is converted with its own ``to_pandas()`` and the results are concatenated with
    ``pandas.concat``.

    Parameters
    ----------
    items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`, optional
        The items to merge, each with a ``to_pandas()`` method.
    paths : list of str, optional
        Unused.
    reader_class : type, optional
        Unused.
    **kwargs
        Additional keyword arguments. If ``pandas_read_csv_kwargs`` is present, it is popped out and
        forwarded as-is to each item's own ``to_pandas()`` call, and everything else in ``kwargs`` is
        passed to ``pandas.concat`` (overriding the default ``ignore_index=True``). If it is absent, all
        of ``kwargs`` is forwarded to ``to_pandas()`` as ``pandas_read_csv_kwargs`` *and* also passed to
        ``pandas.concat`` unchanged -- so in that case every key must be one ``pandas.concat`` (not just
        ``read_csv``) accepts.

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
    return pd.concat([d.to_pandas(pandas_read_csv_kwargs=pandas_read_csv_kwargs) for d in items], **options)
