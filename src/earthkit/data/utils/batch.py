# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta
from abc import abstractmethod


class Iter(metaclass=ABCMeta):
    def __init__(self, data, create=None):
        self.data = data
        self.create = create

    @staticmethod
    def _create(obj, batch):
        if hasattr(obj, "from_list"):
            return obj.from_list
        elif hasattr(obj, "from_fields"):
            return obj.from_fields
        elif len(batch) > 0 and hasattr(batch[0], "to_fieldlist"):
            return batch[0].to_fieldlist

        return lambda x: x

    @abstractmethod
    def _iterator(self, data):
        pass

    @abstractmethod
    def _from_batch(self, obj, batch):
        pass

    @abstractmethod
    def _metadata(self, data, keys):
        pass

    def batched(self, n):
        if n < 1:
            raise ValueError("n must be at least one")

        from itertools import islice

        it = self._iterator(self.data)
        while batch := tuple(islice(it, n)):
            yield self._from_batch(self.data, batch)

    def group_by(self, *args, sort=True):
        keys = self._flatten(args)

        r = self.data.order_by(*keys) if sort else self.data

        from itertools import groupby

        it = self._iterator(r)
        for batch in groupby(it, self._metadata(r, keys)):
            batch = list(batch[1])
            yield self._from_batch(r, batch)

    def _flatten(self, keys):
        _keys = []
        for v in keys:
            if isinstance(v, str):
                _keys.append(v)
            elif isinstance(v, (tuple, list)):
                _keys.extend(v)
        return _keys


class BasicIter(Iter):
    def _iterator(self, data):
        return iter(data)

    def _from_batch(self, obj, batch):
        if self.create is None:
            self.create = self._create(obj, batch)
        return self.create(batch)

    def _metadata(self, data, keys):
        return lambda f: f._attributes(keys)


class IndexedIter(Iter):
    def _iterator(self, data):
        print(f"{data=} {len(data)}")
        return iter(range(len(data)))

    def _from_batch(self, obj, batch):
        if len(batch) >= 2:
            batch = slice(batch[0], batch[-1] + 1)
        return obj[batch]

    def _metadata(self, data, keys):
        return lambda idx: data[idx]._attributes(keys)


def batched(data, n, mode="iter", create=None):
    it = _ITERS.get(mode, None)
    if it is not None:
        return it(data, create=create).batched(n)
    else:
        raise ValueError(f"invalid mode={mode}")


def group_by(data, *args, mode="iter", sort=True, create=None):
    it = _ITERS.get(mode, None)
    if it is not None:
        return it(data, create=create).group_by(*args, sort=sort)
    else:
        raise ValueError(f"invalid mode={mode}")


_ITERS = {"iter": BasicIter, "indexed": IndexedIter}
