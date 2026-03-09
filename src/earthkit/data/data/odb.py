# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .source import SourceData


class ODBData(SourceData):
    _TYPE_NAME = "ODB"

    @property
    def available_types(self):
        return [self._PANDAS]

    def describe(self):
        return f"ODB data from {self._reader.path}"

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_target(self, target, *args, **kwargs):
        if target == "file":
            return self._reader.to_target(target, *args, **kwargs)
        else:
            from earthkit.data import to_target

            return to_target(target, *args, data=self._reader, **kwargs)
