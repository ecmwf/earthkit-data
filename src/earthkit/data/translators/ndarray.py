# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import numpy as np

from . import Translator


class NumpyNDArrayTranslator(Translator):
    """Wrapper around an xarray `DataArray`, offering polymorphism and
    convenience methods.
    """

    _name = "numpy.ndarray"

    def __init__(self, data, *args, **kwargs):
        super().__init__(data.to_numpy(*args, **kwargs))

    def __call__(self):
        return self._data


def translator(data, cls, *args, **kwargs):
    if cls in [np.ndarray]:
        return NumpyNDArrayTranslator(data, *args, **kwargs)

    return None
