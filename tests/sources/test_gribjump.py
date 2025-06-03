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


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_expand_dict_with_lists():
    from earthkit.data.sources.gribjump import expand_dict_with_lists

    request = {
        "b": ["hello", "world"],
        "a": [1, 2, 3],
        "c": 5,
    }
    expected_dicts = [
        {"a": 1, "b": "hello", "c": 5},
        {"a": 1, "b": "world", "c": 5},
        {"a": 2, "b": "hello", "c": 5},
        {"a": 2, "b": "world", "c": 5},
        {"a": 3, "b": "hello", "c": 5},
        {"a": 3, "b": "world", "c": 5},
    ]

    expanded_requests = expand_dict_with_lists(request)
    assert expanded_requests == expected_dicts

    assert expand_dict_with_lists({}) == [{}]
    assert expand_dict_with_lists({"a": 1}) == [{"a": 1}]
    assert expand_dict_with_lists({"a": 1, "b": 2}) == [{"a": 1, "b": 2}]

    with pytest.raises(ValueError, match="Cannot expand dictionary with empty list"):
        expand_dict_with_lists({"a": 1, "b": []})


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
    ds = from_source("file", earthkit_test_data_file("t_time_series.grib"))
    for f in ds:
        setup_fdb_with_gribjump.archive(f.message())
    setup_fdb_with_gribjump.flush()
    yield setup_fdb_with_gribjump


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_ranges(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    source = from_source("gribjump", request, ranges=[(0, 1), (10, 12)])
    arr = source.to_numpy()

    assert arr is not None and isinstance(arr, np.ndarray)
    assert arr.shape == (2, 3)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_mask(seed_fdb):
    import numpy as np
    import xarray as xr

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    mask = np.eye(7, 12, dtype=bool)
    source = from_source("gribjump", request, mask=mask)
    arr = source.to_numpy()
    ds = source.to_xarray()

    ds_expected = xr.Dataset(
        {"129": (("step", "index"), arr)},
        coords={
            "step": np.array([0, 21600000000000], dtype="timedelta64[ns]"),
            "index": np.array([0, 13, 26, 39, 52, 65, 78]),
        },
        attrs={
            "class": "od",
            "date": "20201221",
            "domain": "g",
            "expver": "0001",
            "levelist": "1000",
            "levtype": "pl",
            "stream": "oper",
            "time": "1200",
            "type": "fc",
            "Conventions:": "CF-1.8",
            "institution": "ECMWF",
        },
    )

    assert arr is not None and isinstance(arr, np.ndarray)
    assert arr.shape == (2, 7)
    xr.testing.assert_equal(ds, ds_expected)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_with_indices(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
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
    arr = source.to_numpy()

    assert arr is not None and isinstance(arr, np.ndarray)
    assert arr.shape == (2, 7)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_source_against_manually_masked_grid(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
        "levelist": "1000",
        "levtype": "pl",
        "param": "129",
        "step": [0, 6],
        "stream": "oper",
        "time": "1200",
        "type": "fc",
    }

    mask = (np.eye(7, 12, dtype=bool) | np.eye(7, 12, k=1, dtype=bool)).ravel()

    gj_source = from_source("gribjump", request, mask=mask)
    file_source = from_source("file", earthkit_test_data_file("t_time_series.grib"))

    expected_arr = file_source.sel(step=[0, 6], param="z").to_numpy().reshape(2, -1)[:, mask]
    extracted_arr = gj_source.to_numpy()

    assert np.allclose(expected_arr, extracted_arr)


@pytest.mark.skipif(NO_GRIBJUMP, reason="pygribjump or pyfdb not available")
def test_gribjump_selection(seed_fdb):
    import numpy as np

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
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
def test_gribjump_with_mixed_types_in_lists(seed_fdb):

    request = {
        "class": "od",
        "date": "20201221",
        "domain": "g",
        "expver": "0001",
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
        "expver": "0001",
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


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
