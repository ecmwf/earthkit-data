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
from earthkit.data.testing import NO_HDA

REQ_1 = {
    "dataset_id": "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
    "startdate": "2019-01-01T00:00:00.000Z",
    "enddate": "2019-01-01T2:59:59.999Z",
}

REQ_2 = {
    "dataset_id": "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
    "startdate": "2019-01-01T03:00:00.000Z",
    "enddate": "2019-01-01T06:59:59.999Z",
}


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to WEKEO")
@pytest.mark.parametrize("prompt", [True, False])
def test_wekeo_download_single_1(prompt):
    ds = from_source(
        "wekeo",
        "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
        prompt=prompt,
        request=REQ_1,
    )
    assert len(ds) == 1


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to WEKEO")
@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((REQ_1,), None, {}),
        (([REQ_1]), None, {}),
        ((), REQ_1, {}),
        ((), [REQ_1], {}),
        ((), None, REQ_1),
    ],
)
def test_wekeo_download_single_2(_args, req, _kwargs):
    ds = from_source(
        "wekeo",
        "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
        *_args,
        prompt=False,
        request=req,
        **_kwargs,
    )
    assert len(ds) == 1


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_HDA, reason="No access to WEKEO")
@pytest.mark.parametrize("_args,req,_kwargs", [((REQ_1, REQ_2), None, {}), ((), [REQ_1, REQ_2], {})])
def test_wekeo_download_multi(_args, req, _kwargs):
    ds = from_source(
        "wekeo",
        "EO:CLMS:DAT:CLMS_GLOBAL_BA_300M_V3_MONTHLY_NETCDF",
        *_args,
        request=req,
        prompt=False,
        **_kwargs,
    )
    assert len(ds) == 2


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
