# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
from . import Translator


class StrTranslator(Translator):
    _name = "str"

    def __init__(self, data, *args, **kwargs):
        super().__init__(data.to_string(*args, **kwargs))

    def __call__(self):
        return self._data


def translator(data, cls, *args, **kwargs):
    if cls in [str, "string", "str"]:
        return StrTranslator(data, *args, **kwargs)

    return None
