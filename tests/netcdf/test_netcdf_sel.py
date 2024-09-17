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

from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "params,expected_meta,metadata_keys",
    [
        (dict(variable="u", level=700), [["u", 700]], []),
        (
            dict(variable=["t", "u"], level=[700, 500]),
            [
                ["t", 700],
                ["t", 500],
                ["u", 700],
                ["u", 500],
            ],
            ["variable", "level"],
        ),
        (dict(variable="w"), [], []),
        (dict(INVALIDKEY="w"), [], []),
        (
            dict(
                variable=["t"],
                level=[500, 700],
                valid_datetime="2018-08-01T12:00:00",
            ),
            [
                ["t", 700, "2018-08-01T12:00:00"],
                ["t", 500, "2018-08-01T12:00:00"],
            ],
            ["variable", "level", "valid_datetime"],
        ),
        (
            dict(
                variable=["t"],
                level=[500, 700],
                date=20180801,
                time=1200,
            ),
            [
                ["t", 700, 20180801, 1200],
                ["t", 500, 20180801, 1200],
            ],
            ["variable", "level", "date", "time"],
        ),
    ],
)
def test_netcdf_sel_single_file_1(mode, params, expected_meta, metadata_keys):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    g = f.sel(**params)
    assert len(g) == len(expected_meta)
    if len(expected_meta) > 0:
        keys = list(params.keys())
        if metadata_keys:
            keys = metadata_keys

        assert g.metadata(keys) == expected_meta
    return


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
