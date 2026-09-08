# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def concat(*args):
    """Concatenate multiple objects into a single one, preserving their level of abstraction.

    Internally, this combines the inputs using the ``"multi"`` source (see
    :class:`~earthkit.data.sources.multi.MultiSource` and :ref:`mergers`), then adjusts the result to match the
    level of abstraction of the inputs: if any input was a :ref:`Data object <data-object>`, the result is
    a ``Data`` object too; if all inputs were lower-level :class:`~earthkit.data.core.field.Field` or
    :class:`~earthkit.data.sources.Source` objects (e.g. a :class:`~earthkit.data.core.fieldlist.FieldList`,
    which is itself a ``Source``), the result is unwrapped back to a plain ``Source``.

    Parameters
    ----------
    *args : Field, Data object, or Source
        The objects to concatenate, at least one. Passing a single argument returns it unchanged, whatever
        its type. With more than one argument, each item must be one of:

        - a :class:`~earthkit.data.core.field.Field`, converted to a single-field
          :class:`~earthkit.data.core.fieldlist.FieldList` before concatenation;
        - a :ref:`Data object <data-object>` (e.g. as returned by :func:`earthkit.data.from_source`),
          unwrapped to its underlying :class:`~earthkit.data.sources.Source` via its ``_source`` attribute;
        - a :class:`~earthkit.data.sources.Source` (e.g. a ``FieldList``), used as is.

        An argument of any other type is silently ignored.

    Returns
    -------
    :class:`~earthkit.data.sources.Source` or :ref:`Data object <data-object>`
        A single object combining all the inputs. It is a ``Data`` object if at least one input was one;
        otherwise it is the underlying ``Source``.

    Raises
    ------
    ValueError
        If no arguments are given, if a ``Data`` argument has no ``_source`` attribute to unwrap it with,
        or if the combined result could not be resolved to a valid object.

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

    # TODO: make it more flexible
    # currently we assume all arguments are sources
    from earthkit.data import Field
    from earthkit.data.data import Data
    from earthkit.data.sources import Source

    has_data = False
    data = []
    for arg in args:
        if isinstance(arg, Field):
            data.append(arg.to_fieldlist())
        elif isinstance(arg, Data):
            has_data = True
            if hasattr(arg, "_source"):
                data.append(arg._source)
            else:
                raise ValueError(f"Cannot concatenate type={type(arg)} object")
        elif isinstance(arg, Source):
            data.append(arg)

    from earthkit.data.sources import from_source

    result = from_source("multi", *data)

    if not has_data:
        if result is None or not hasattr(result, "_source"):
            raise ValueError("concat could not create a valid Data object from the provided arguments")
        return result._source
    return result
