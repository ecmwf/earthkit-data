# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def concat(*args):
    """Concatenate multiple data objects into a single one."""
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
