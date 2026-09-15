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
    fs = [s.to_fieldlist() for s in sources]
    from earthkit.data.mergers import merge_by_class

    merged = merge_by_class(fs)
    if merged is not None:
        return merged.mutate()

    return None
