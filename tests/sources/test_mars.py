#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

import pytest

from earthkit.data import config
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import NO_MARS
from earthkit.data.testing import NO_MARS_API
from earthkit.data.testing import NO_MARS_DIRECT
from earthkit.data.testing import WRITE_TO_FILE_METHODS
from earthkit.data.testing import write_to_file

YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")


REQ_1 = dict(
    param="2t",
    levtype="sfc",
    area=[50, -50, 20, 50],
    grid=[2, 2],
    date="2023-05-10",
    split_on="param",
)

REQ_2 = dict(
    param="msl",
    levtype="sfc",
    area=[50, -50, 20, 50],
    grid=[2, 2],
    date="2023-05-10",
    split_on="param",
)


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
@pytest.mark.parametrize("prompt", [True, False])
def test_mars_grib_1_prompt(prompt):
    s = from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        prompt=prompt,
        date="2023-05-10",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_split_on():
    ds = from_source(
        "mars",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="2023-05-10",
        split_on="param",
    )
    assert len(ds) == 2
    assert ds.metadata("param") == ["2t", "msl"]
    assert not hasattr(ds, "path")
    assert len(ds._indexes) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.parametrize("_args,req,_kwargs", [((REQ_1, REQ_2), None, {}), ((), [REQ_1, REQ_2], {})])
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_multi(_args, req, _kwargs):
    ds = from_source(
        "mars",
        *_args,
        request=req,
        **_kwargs,
    )
    assert len(ds) == 2
    assert ds.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_parallel():
    with config.temporary("number-of-download-threads", 4):

        req = dict(param="t", levelist=[925, 850, 700, 500], date=YESTERDAY, split_on="levelist")

        ds = from_source(
            "mars",
            request=req,
        )
        assert len(ds) == 4
        assert ds.metadata("param") == ["t"] * 4
        assert ds.metadata("levelist") == [925, 850, 700, 500]
        assert not hasattr(ds, "path")
        assert len(ds._indexes) == 4


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_expect_any_1():
    ds = from_source(
        "mars",
        expect="any",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="1054-05-10",
    )

    assert len(ds) == 0


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_expect_any_2():
    with pytest.raises(Exception):
        from_source(
            "mars",
            param=["2t", "msl"],
            levtype="sfc",
            area=[50, -50, 20, 50],
            grid=[2, 2],
            date="1054-05-10",
        )


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_log_1():
    s = from_source(
        "mars",
        prompt=False,
        log="default",
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="2023-05-10",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS, reason="No access to MARS")
def test_mars_grib_log_2():
    s = from_source(
        "mars",
        prompt=False,
        log=None,
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="2023-05-10",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(not NO_MARS_DIRECT or NO_MARS_API, reason="No access to MARS")
def test_mars_grib_log_3():
    res = 0

    def _my_log(msg):
        nonlocal res
        res = 1

    s = from_source(
        "mars",
        prompt=False,
        log=_my_log,
        param=["2t", "msl"],
        levtype="sfc",
        area=[50, -50, 20, 50],
        grid=[2, 2],
        date="2023-05-10",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_MARS_DIRECT and not NO_MARS_API, reason="No access to MARS")
def test_mars_grib_log_4():
    with temp_file() as tmp:
        with open(tmp, "w") as f:
            s = from_source(
                "mars",
                prompt=False,
                log={"stdout": f},
                param=["2t", "msl"],
                levtype="sfc",
                area=[50, -50, 20, 50],
                grid=[2, 2],
                date="2023-05-10",
            )
            assert len(s) == 2

        t = ""
        with open(tmp) as f:
            t = f.read()

        assert t


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
def test_mars_grib_save(write_method):
    ds = from_source(
        "mars",
        param="2t",
        levtype="sfc",
        grid=[30, 30],
        date=-1,
    )
    assert len(ds) == 1

    with temp_file() as tmp:
        write_to_file(write_method, tmp, ds)

        ds1 = from_source("file", tmp)
        assert len(ds1) == 1


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
