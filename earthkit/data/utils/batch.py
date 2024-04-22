# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def flatten(keys):
    _keys = []
    for v in keys:
        if isinstance(v, str):
            _keys.append(v)
        elif isinstance(v, (tuple, list)):
            _keys.extend(v)
    return _keys


def create_maker(obj, batch):
    if hasattr(obj, "from_list"):
        return obj.from_list
    elif hasattr(obj, "from_fields"):
        return obj.from_fields
    elif len(batch) > 0 and hasattr(batch[0], "to_fieldlist"):
        return batch[0].to_fieldlist

    return lambda x: x


def batched_iter(obj, n, maker=None):
    if n < 1:
        raise ValueError("n must be at least one")

    from itertools import islice

    it = iter(obj)
    while batch := tuple(islice(it, n)):
        if maker is None:
            maker = create_maker(obj, batch)
        yield maker(batch)


def batched_indexed(obj, n):
    if n < 1:
        raise ValueError("n must be at least one")

    from itertools import islice

    it = iter(range(len(obj)))
    while batch := tuple(islice(it, n)):
        if len(batch) >= 2:
            batch = slice(batch[0], batch[-1] + 1)
        yield obj[batch]


def batched(obj, n, mode="iter", maker=None):
    if n < 1:
        raise ValueError("n must be at least one")

    if mode == "iter":
        return batched_iter(obj, n, maker=maker)
    elif mode == "indexed":
        return batched_indexed(obj, n)
    raise ValueError(f"invalid mode={mode}")


def group_by_indexed(obj, *args, sort=True):
    keys = flatten(args)

    r = obj.order_by(*keys) if sort else obj

    def _key(idx):
        return r[idx]._attributes(keys)

    from itertools import groupby

    it = range(len(r))
    for batch in groupby(it, _key):
        batch = list(batch[1])
        yield r[batch]


def group_by_iter(obj, *args, maker=None):
    keys = flatten(args)

    def _key(f):
        return f._attributes(keys)

    from itertools import groupby

    it = iter(obj)
    for batch in groupby(it, _key):
        batch = list(batch[1])
        if maker is None:
            maker = create_maker(obj, batch)
        yield maker(batch)


def group_by(obj, *args, sort=True, mode="iter", maker=None):
    if mode == "iter":
        return group_by_iter(obj, *args, maker=maker)
    elif mode == "indexed":
        return group_by_indexed(obj, *args, sort=sort)
    raise ValueError(f"invalid mode={mode}")
