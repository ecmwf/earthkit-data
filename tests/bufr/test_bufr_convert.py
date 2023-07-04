#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

assert_frame_equal = pd.testing.assert_frame_equal


@pytest.mark.parametrize("_kwargs", [{}, {"filters": {}}])
def test_bufr_to_pandas_no_filters(_kwargs):
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))

    res = ds.to_pandas(columns=["latitude", "longitude", "WMO_station_id"], **_kwargs)

    row_ref_0 = {"latitude": 67.37, "longitude": 26.63, "WMO_station_id": 2836}
    row_ref_9 = {"latitude": 60.82, "longitude": 23.50, "WMO_station_id": 2963}

    ref_0 = pd.DataFrame(row_ref_0, index=[0])
    ref_9 = pd.DataFrame(row_ref_9, index=[9])

    assert len(res) == 10
    assert list(res.columns) == ["latitude", "longitude", "WMO_station_id"]
    assert_frame_equal(res[0:1], ref_0[res.columns])
    assert_frame_equal(res[9:10], ref_9[res.columns])


def test_bufr_to_pandas_filters():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))

    res = ds.to_pandas(
        columns=["latitude", "longitude", "WMO_station_id"],
        filters={"WMO_station_id": [2836, 2963]},
    )

    ref = pd.DataFrame.from_dict(
        {
            "latitude": [67.37, 60.82],
            "longitude": [26.63, 23.50],
            "WMO_station_id": [2836, 2963],
        }
    )
    assert_frame_equal(res, ref[res.columns])


def test_bufr_to_pandas_multi():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")) + from_source(
        "file", earthkit_examples_file("synop_10.bufr")
    )

    res = ds.to_pandas(
        columns=["latitude", "longitude", "WMO_station_id"],
    )

    assert len(res) == 20


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
