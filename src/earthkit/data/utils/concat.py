# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def concat(*args):
    if len(args) == 0:
        raise ValueError("concat requires at least one argument")

    first = args[0]
    if len(args) == 1:
        return first

    # TODO: make it more flexible
    # currently we assume all arguments are sources
    from earthkit.data.sources import from_source

    return from_source("multi", *args)
