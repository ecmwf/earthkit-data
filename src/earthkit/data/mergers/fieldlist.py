# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.core.field import Field
from earthkit.data.core.fieldlist import FieldList


def merge(
    items=None,
    paths=None,
    reader_class=None,
    **kwargs,
):
    """Merge ``items`` into a single fieldlist.

    Each item is first turned into its own :class:`~earthkit.data.core.fieldlist.FieldList`: a
    :class:`~earthkit.data.core.field.Field` is wrapped with its own ``to_fieldlist()``; a ``FieldList`` is
    used as is; a ``str`` is treated as a file path and read via ``from_source("file", item)``; anything
    else with a ``to_fieldlist`` method (e.g. a :ref:`Data object <data-object>`) has that called. The
    resulting fieldlists are then merged using :func:`earthkit.data.mergers.merge_by_class`, and the result
    is mutated to its final form.

    Parameters
    ----------
    items : list of Field, FieldList, str, or anything with a ``to_fieldlist()`` method, optional
        The inputs to merge.
    paths : list of str, optional
        Unused.
    reader_class : type, optional
        Unused.
    **kwargs
        Passed to ``to_fieldlist()`` when an item is a ``str`` path or otherwise has its own
        ``to_fieldlist`` method called; unused for items that are already a ``Field``/``FieldList``.

    Returns
    -------
    :class:`earthkit.data.core.fieldlist.FieldList` or None
        The merged fieldlist, or None if the sources could not be merged.

    Raises
    ------
    ValueError
        If an item is none of the accepted types above.
    """
    fl = []
    for d in items:
        if isinstance(d, Field):
            fl.append(d.to_fieldlist())
        elif isinstance(d, FieldList):
            fl.append(d)
        elif isinstance(d, str):
            fl.append(from_source("file", d).to_fieldlist(**kwargs))
        elif hasattr(d, "to_fieldlist"):
            fl.append(d.to_fieldlist(**kwargs))
        else:
            raise ValueError(f"Cannot convert object of type={type(d)} to a FieldList")

    from earthkit.data.mergers import merge_by_class

    merged = merge_by_class(fl)
    if merged is not None:
        return merged.mutate()

    return None
