# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def concat(*args):
    """Concatenate multiple objects into a single one.

    With a single argument, returns it unchanged, whatever its type. With more than one, tries to combine
    them at decreasing levels of abstraction, keeping the first attempt that succeeds:

    1. as a fieldlist (see :func:`_try_concat_as_fieldlist`): if every argument is a
       :class:`~earthkit.data.core.field.Field` or a :class:`~earthkit.data.core.fieldlist.FieldList`,
       merges them via the ``"multi"`` source (see :class:`~earthkit.data.sources.multi.MultiSource` and
       :ref:`mergers`) and returns the resulting FieldList.
    2. as a source (see :func:`_try_concat_as_source`): otherwise, if every argument is itself a
       :class:`~earthkit.data.sources.Source`, or a :ref:`Data object <data-object>` whose ``_source``
       attribute is one, merges those sources via the ``"multi"`` source and returns the underlying
       ``Source`` of the result. Note that this discards the ``Data`` wrapper even when one or more
       arguments were ``Data`` objects, as long as they all had an underlying source to fall back on.
    3. as Data objects (see :func:`_concat_as_data`): otherwise, converts every argument that is not
       already a ``Data`` object with its own ``to_data_object()``, and combines the resulting ``Data``
       objects directly into a :class:`~earthkit.data.data.multi.MultiData` -- this is the only path that
       reliably preserves a ``Data`` result, and is really only reached when at least one argument (e.g.
       one created by :func:`earthkit.data.from_object`) has no underlying source at all.

    Parameters
    ----------
    *args : Field, FieldList, Source, or Data object
        The objects to concatenate, at least one.

    Returns
    -------
    :class:`~earthkit.data.core.fieldlist.FieldList`, :class:`~earthkit.data.sources.Source`, or
    :ref:`Data object <data-object>`
        A single object combining all the inputs, at whichever level of abstraction the first successful
        attempt above operated at -- see there for which one that is.

    Raises
    ------
    ValueError
        If no arguments are given, or if none of the three combination attempts above could handle them.

    Examples
    --------
    >>> ds = concat(from_source("file", "a.grib"), from_source("file", "b.grib"))

    >>> fl = concat(from_source("file", "a.grib").to_fieldlist(), from_source("file", "b.grib").to_fieldlist())
    """
    if len(args) == 0:
        raise ValueError("concat requires at least one argument")

    first = args[0]
    if len(args) == 1:
        return first

    from earthkit.data import Field
    from earthkit.data.data import Data

    # convert all fields to fieldlists
    inputs = []
    for d in args:
        if isinstance(d, Field):
            inputs.append(d.to_fieldlist())
        else:
            inputs.append(d)

    # handle the case when all the inputs are field/fieldlist
    result = _try_concat_as_fieldlist(*inputs)
    if result is not None:
        return result

    # handle the case when all the inputs are Source objects or compatible
    # with Source (e.g. Data objects with a _source attribute). An existing
    # fieldlist implementation is also a source.
    result = _try_concat_as_source(*inputs)
    if result is not None:
        if isinstance(result, Data) and hasattr(result, "_source") and result._source is not None:
            return result._source
        return result

    result = _concat_as_data(*inputs)
    if result is not None:
        return result

    raise ValueError("concat could not create a valid Data object from the provided arguments")


def _try_concat_as_fieldlist(*args):
    """Attempt to concatenate ``args`` as a single :class:`~earthkit.data.core.fieldlist.FieldList`.

    Succeeds only if every argument is a :class:`~earthkit.data.core.field.Field` (converted to a
    single-field FieldList) or already a FieldList. :func:`concat` already converts every ``Field``
    argument to a ``FieldList`` before calling this, so the ``Field`` branch below is effectively
    unreachable from there; it is kept so this function gives the same result when called on its own.

    Parameters
    ----------
    *args : Field or FieldList
        The candidate arguments.

    Returns
    -------
    :class:`~earthkit.data.core.fieldlist.FieldList` or None
        The merged FieldList, or None as soon as an argument is neither a ``Field`` nor a ``FieldList``,
        signalling the caller to fall back to a lower level of abstraction (see :func:`concat`).
    """
    from earthkit.data import Field, FieldList

    fl = []
    for arg in args:
        if isinstance(arg, Field):
            fl.append(arg.to_fieldlist())
        elif isinstance(arg, FieldList):
            fl.append(arg)
        else:
            return None

    from earthkit.data.sources import from_source

    result = from_source("multi", *fl)
    return result.to_fieldlist()


def _try_concat_as_source(*args):
    """Attempt to concatenate ``args`` as a single :class:`~earthkit.data.sources.Source`.

    Succeeds only if every argument is itself a ``Source``, or a :ref:`Data object <data-object>` whose
    ``_source`` attribute is one. On success, the underlying sources are combined via the ``"multi"``
    source (see :class:`~earthkit.data.sources.multi.MultiSource` and :ref:`mergers`); the caller
    (:func:`concat`) then unwraps the resulting ``Data`` object back to its own underlying ``Source``.

    Parameters
    ----------
    *args : Source, or Data object with a ``Source`` in ``_source``
        The candidate arguments.

    Returns
    -------
    :ref:`Data object <data-object>` or None
        The ``Data`` object returned by ``from_source("multi", ...)`` over the underlying sources, or
        None as soon as an argument has no usable underlying source, signalling the caller to fall back
        to combining the arguments as plain ``Data`` objects instead (see :func:`concat`).
    """
    from earthkit.data.sources import Source

    source = []
    for arg in args:
        if isinstance(arg, Source):
            source.append(arg)
        elif hasattr(arg, "_source") and isinstance(arg._source, Source):
            source.append(arg._source)
        else:
            return None

    from earthkit.data.sources import from_source

    return from_source("multi", *source)


def _concat_as_data(*args):
    """Concatenate ``args`` as :ref:`Data objects <data-object>`, converting any that aren't already one.

    Unlike :func:`_try_concat_as_fieldlist`/:func:`_try_concat_as_source`, this cannot fail: it is the
    final fallback in :func:`concat`, reached once neither of the higher-abstraction attempts succeeded,
    and always combines the (possibly converted) arguments into a single ``MultiData``.

    Parameters
    ----------
    *args : Data object, or anything with a ``to_data_object()`` method
        The arguments to combine; each one that is not already a ``Data`` object is converted with its own
        ``to_data_object()``.

    Returns
    -------
    :class:`~earthkit.data.data.multi.MultiData`
    """
    from earthkit.data.data import Data

    data = []
    for arg in args:
        if isinstance(arg, Data):
            data.append(arg)
        else:
            data.append(arg.to_data_object())

    from earthkit.data.data.multi import MultiData

    return MultiData(data)
