# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

from . import Dataset


class TestDataset(Dataset):
    def __init__(self, param="t"):
        self.source = from_source("file", earthkit_examples_file("tuv_pl.grib"))


dataset = TestDataset
