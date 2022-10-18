# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import numpy as np

from emohawk import Data


class ListWrapper(Data):
    def to_numpy(self):
        return np.array(self.source)


def wrapper(data, *args, **kwargs):
    if isinstance(data, list):
        return ListWrapper(data, *args, **kwargs)
    return None
