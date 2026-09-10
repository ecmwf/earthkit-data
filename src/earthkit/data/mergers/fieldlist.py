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
    data=None,
    paths=None,
    reader_class=None,
    **kwargs,
):
    """Merge ``data`` into a single fieldlist.

    Each source's ``to_fieldlist()`` result is merged using :func:`earthkit.data.mergers.merge_by_class`,
    and the result is mutated to its final form.

    Parameters
    ----------
    data : list of :class:`earthkit.data.sources.Source`, optional
        The inputs to merge.
    paths : list of str, optional
        Unused.
    reader_class : type, optional
        Unused.
    **kwargs
        Unused.

    Returns
    -------
    :class:`earthkit.data.core.fieldlist.FieldList` or None
        The merged fieldlist, or None if the sources could not be merged.
    """
    fl = []
    for d in data:
        if isinstance(d, Field):
            fl.append(d.to_fieldlist())
        elif isinstance(d, FieldList):
            fl.append(d)
        elif isinstance(d, str):
            fl.append(from_source("file", d).to_fieldlist(**kwargs))
        else:
            fl.append(d.to_fieldlist(**kwargs))

    from earthkit.data.mergers import merge_by_class

    merged = merge_by_class(fl)
    if merged is not None:
        return merged.mutate()

    return None
