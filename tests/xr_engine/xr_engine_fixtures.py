#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data import from_source
from earthkit.data.utils.xarray.fieldlist import WrappedFieldList


def load_fieldlist(d):
    assert isinstance(d, dict)
    r = []

    prototype = {
        "gridType": "regular_ll",
        "Nx": 2,
        "Ny": 3,
        "distinctLatitudes": [-10.0, 0.0, 10.0],
        "distinctLongitudes": [0.0, 10.0],
        "values": [[1, 2], [3, 4], [5, 6]],
    }

    from itertools import product

    for x in list(product(*d.values())):
        y = dict(zip(d.keys(), x))
        r.append({**y, **prototype})

    return from_source("list-of-dicts", r)


def load_wrapped_fieldlist(d, profile, **kwargs):
    if isinstance(d, list):
        ds = []
        for x in d:
            ds.extend(load_fieldlist(x))
    elif isinstance(d, dict):
        ds = load_fieldlist(d)
    else:
        raise ValueError(f"Invalid data type={type(d)}")

    return WrappedFieldList(ds, keys=profile.index_keys, **kwargs)
