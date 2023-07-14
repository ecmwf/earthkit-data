# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class Metadata(metaclass=ABCMeta):
    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def items(self):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def get(self, key, *args):
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class RawMetadata(Metadata):
    def __init__(self, d):
        self._d = d

    def keys(self):
        return self._d.keys()

    def items(self):
        return self._d.items()

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def get(self, key, *args):
        if len(args) == 1:
            return self._d.get(key, args[0])
        elif len(args) == 0:
            if key in self._d:
                return self._d.get(key)
            else:
                raise KeyError
        else:
            raise ValueError

    def update(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)
