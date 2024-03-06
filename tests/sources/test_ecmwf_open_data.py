#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_source
from earthkit.data.testing import NO_EOD


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod():
    ds = from_source(
        "ecmwf-open-data",
        param=["2t", "msl"],
        levtype="sfc",
    )
    assert len(ds) == 2
    assert ds.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
@pytest.mark.parametrize("model", ["ifs", "aifs"])
def test_eod_model(model):
    ds = from_source(
        "ecmwf-open-data",
        model=model,
        param="t",
        levelist=500,
    )
    assert len(ds) == 1
    assert ds[0].metadata(["param", "level"]) == ["t", 500]


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
