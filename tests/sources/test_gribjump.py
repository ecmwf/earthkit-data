#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import shutil
from pathlib import Path

import pytest
import yaml

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_env
from earthkit.data.testing import NO_GRIBJUMP
from earthkit.data.testing import earthkit_test_data_file


@pytest.fixture
def setup_fdb_with_gribjump():
    import pyfdb

    with temp_directory() as tmpdir:
        fdb_dir = Path(tmpdir) / "fdb"
        fdb_dir.mkdir(exist_ok=True)

        # Copy of FDB schema
        fdb_schema = earthkit_test_data_file("fdb_schema.txt")
        shutil.copy(fdb_schema, fdb_dir / "schema")

        # FDB config
        fdb_config = {
            "type": "local",
            "engine": "toc",
            "schema": str(fdb_dir / "schema"),
            "spaces": [{"handler": "Default", "roots": [{"path": str(fdb_dir)}]}],
        }
        fdb_config_path = fdb_dir / "config.yaml"
        fdb_config_path.write_text(yaml.dump(fdb_config))

        # Gribjump config
        gj_config = {
            "plugin": {
                "select": "class=(.)",
            }
        }
        gj_config_path = fdb_dir / "gribjump.yaml"
        gj_config_path.write_text(yaml.dump(gj_config))

        with temp_env(
            FDB5_CONFIG_FILE=str(fdb_config_path),
            FDB_ENABLE_GRIBJUMP="1",
            FDB_HOME=str(fdb_dir),
            GRIBJUMP_CONFIG_FILE=str(gj_config_path),
            GRIBJUMP_IGNORE_GRID="1",
        ):
            fdb = pyfdb.FDB(config=fdb_config)
            yield fdb


@pytest.fixture
def seed_fdb(setup_fdb_with_gribjump):
    ds = from_source("file", earthkit_test_data_file("t_gribjump.grib"))
    for f in ds:
        setup_fdb_with_gribjump.archive(f.message())
    setup_fdb_with_gribjump.flush()
    yield setup_fdb_with_gribjump


@pytest.fixture
def ranges():
    return dict(ranges=[(0, 1), (5, 9), (25, 27)])


@pytest.fixture
def indices():
    import numpy as np

    return dict(indices=np.array([0, 5, 6, 7, 8, 25, 26]))


@pytest.fixture
def mask():
    import numpy as np

    mask = np.zeros((7, 12), dtype=bool)
    mask[0, 0] = True
    mask[0, 5:9] = True
    mask[2, 1:3] = True
    mask = mask.ravel()
    return dict(mask=mask)


@pytest.fixture
def arr_expected():
    import numpy as np

    arr_expected = np.array(
        [
            [
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1607.31591797,
                1721.81591797,
            ],
            [
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1702.31201172,
                1887.18701172,
            ],
        ]
    )
    return arr_expected


@pytest.fixture
def ds_expected_with_coords():
    import numpy as np
    import xarray as xr

    arr_expected = np.array(
        [
            [
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1743.06591797,
                1607.31591797,
                1721.81591797,
            ],
            [
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1641.43701172,
                1702.31201172,
                1887.18701172,
            ],
        ]
    )
    latitude_expected = np.array(
        [
            90.0,
            90.0,
            90.0,
            90.0,
            90.0,
            30.0,
            30.0,
        ]
    )
    longitude_expected = np.array(
        [
            0.0,
            150.0,
            180.0,
            210.0,
            240.0,
            30.0,
            60.0,
        ]
    )
    ds_expected = xr.Dataset(
        {"129": (("step", "index"), arr_expected)},
        coords={
            "step": np.array([0, 21600000000000], dtype="timedelta64[ns]"),
            "index": np.array([0, 5, 6, 7, 8, 25, 26]),
            "latitude": ("index", latitude_expected),
            "longitude": ("index", longitude_expected),
        },
        attrs={
            "class": "od",
            "date": "20201221",
            "domain": "g",
            "expver": "xxxx",
            "levelist": "1000",
            "levtype": "pl",
            "stream": "oper",
            "param": "129",
            "time": "1200",
            "type": "fc",
            "Conventions": "CF-1.8",
            "institution": "ECMWF",
        },
    )
    return ds_expected


@pytest.fixture
def ds_expected(ds_expected_with_coords):
    # Remove coordinates to match the expected output
    ds = ds_expected_with_coords.drop_vars(["latitude", "longitude"])
    return ds


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_split_mars_requests():
    from earthkit.data.sources.gribjump import split_mars_requests

    request = {
        "step": [0, 6, 12],
        "param": ["129", "130"],
        "date": "20230101",
        "time": "1200",
    }
    result = split_mars_requests(request)
    assert result == [
        {"param": "129", "step": 0, "date": "20230101", "time": "1200"},
        {"param": "129", "step": 6, "date": "20230101", "time": "1200"},
        {"param": "129", "step": 12, "date": "20230101", "time": "1200"},
        {"param": "130", "step": 0, "date": "20230101", "time": "1200"},
        {"param": "130", "step": 6, "date": "20230101", "time": "1200"},
        {"param": "130", "step": 12, "date": "20230101", "time": "1200"},
    ]

    assert split_mars_requests({}) == [{}]
    assert split_mars_requests({"a": 1}) == [{"a": 1}]
    assert split_mars_requests({"a": 1, "b": 2}) == [{"a": 1, "b": 2}]

    # Error: empty list
    with pytest.raises(ValueError, match="Cannot expand dictionary with empty list"):
        split_mars_requests({"a": 1, "b": []})

    # Error: unsupported "/" syntax
    with pytest.raises(ValueError, match="Found unsupported list or range using '/'"):
        split_mars_requests({"param": "129/130", "date": "20230101"})

    # Error: mixed types in lists
    request_mixed = {"param": [129, "130"], "date": "20230101"}
    with pytest.raises(TypeError, match="All list values must share the same type"):
        split_mars_requests(request_mixed)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
@pytest.mark.parametrize(
    "mask,expected_ranges",
    [
        ([False, False, False], []),
        ([True, True, False], [(0, 2)]),
        ([False, False, True], [(2, 3)]),
        ([False, False, True, True, False, True, False], [(2, 4), (5, 6)]),
        ([True, False, True, True, True, False, True], [(0, 1), (2, 5), (6, 7)]),
    ],
)
def test_mask_to_ranges(mask, expected_ranges):
    import numpy as np

    from earthkit.data.sources.gribjump import mask_to_ranges

    mask = np.array(mask, dtype=bool)
    result = mask_to_ranges(mask)
    assert result == expected_ranges


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
@pytest.mark.parametrize(
    "mask,error_type",
    [
        ([], ValueError),
        ([1, 0, 1], ValueError),
        ([[False, True], [True, False]], ValueError),
    ],
)
def test_mask_to_ranges_errors(mask, error_type):
    import numpy as np

    from earthkit.data.sources.gribjump import mask_to_ranges

    with pytest.raises(error_type):
        mask_to_ranges(np.array(mask))


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
@pytest.mark.parametrize("method", ["ranges", "indices", "mask"])
def test_gribjump_to_numpy(seed_fdb, arr_expected, method, request):
    import numpy as np

    kwargs = request.getfixturevalue(method)
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    source = from_source("gribjump", mars_request, **kwargs)
    arr = source.to_numpy()

    assert arr is not None and isinstance(arr, np.ndarray)
    assert arr.shape == (2, 7)
    np.testing.assert_array_almost_equal(arr, arr_expected)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
@pytest.mark.parametrize("method", ["ranges", "indices", "mask"])
def test_gribjump_to_xarray_without_coords(seed_fdb, ds_expected, method, request):
    import xarray as xr

    kwargs = request.getfixturevalue(method)
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    source = from_source("gribjump", mars_request, **kwargs)
    ds = source.to_xarray()

    xr.testing.assert_allclose(ds, ds_expected)
    assert ds_expected.attrs == ds.attrs
    assert set(ds_expected.coords.keys()) == set(ds.coords.keys())


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
@pytest.mark.parametrize("method", ["ranges", "indices", "mask"])
def test_gribjump_to_xarray_with_coords(seed_fdb, ds_expected_with_coords, method, request):
    import xarray as xr

    kwargs = request.getfixturevalue(method)
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    source = from_source("gribjump", mars_request, fetch_coords_from_fdb=True, **kwargs)
    ds = source.to_xarray()

    xr.testing.assert_allclose(ds, ds_expected_with_coords)
    assert ds_expected_with_coords.attrs == ds.attrs
    assert set(ds_expected_with_coords.coords.keys()) == set(ds.coords.keys())


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_selection(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    indices = np.array([0, 7, 14, 21, 28, 35, 42])
    source = from_source("gribjump", request, indices=indices)

    arr_orig = source.to_numpy()
    arr_subset = source.sel(step=6).to_numpy()

    assert arr_subset.shape == (1, 7)
    assert np.allclose(arr_orig[[1]], arr_subset)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_to_xarray_with_coords_does_not_fail_for_grids(seed_fdb):
    mars_request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    source = from_source("gribjump", mars_request, fetch_coords_from_fdb=True, indices=[0])
    ds = source.to_xarray()
    assert set(ds.dims) == {"step", "index"}
    assert set(ds.coords) == {"step", "index", "latitude", "longitude"}


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_mixed_types_in_lists(seed_fdb):

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, "6"],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    with pytest.raises(TypeError):
        from_source("gribjump", request, ranges=[(1, 2)])


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_invalid_options(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    with pytest.raises(ValueError, match="Exactly one of"):
        from_source(
            "gribjump",
            request,
        )

    with pytest.raises(ValueError, match="Exactly one of"):
        from_source(
            "gribjump",
            request,
            ranges=[(0, 1), (10, 12)],
            indices=np.array([0, 7, 14, 21, 28, 35, 42]),
        )


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_invalid_mask(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "xxxx",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    with pytest.raises(ValueError, match="Expected 'mask' to be a 1D numpy array"):
        mask = np.array([[True, False], [False, True]], dtype=bool)
        from_source(
            "gribjump",
            request,
            mask=mask,
        )

    with pytest.raises(ValueError, match="Expected 'mask' to be a boolean array"):
        mask = np.array([1, 0, 1], dtype=int)
        from_source(
            "gribjump",
            request,
            mask=mask,
        )

    with pytest.raises(TypeError, match="Expected 'mask' to be a numpy array"):
        mask = [True, False, True]
        from_source(
            "gribjump",
            request,
            mask=mask,
        )


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
