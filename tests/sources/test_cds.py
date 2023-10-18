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
from earthkit.data.testing import NO_CDS


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_grib_1():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_grib_2():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        split_on="variable",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_grib_3():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12/to/2012-12-15",
        time="12:00",
    )
    assert len(s) == 8


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.parametrize(
    "variable1,variable2,expected_vars",
    (
        ("2t", ["2t"], {"t2m"}),
        (["2t", "msl"], ["msl", "2t"], {"t2m", "msl"}),
    ),
)
def test_cds_normalized_request(variable1, variable2, expected_vars):
    base_request = dict(
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        grid=[2, 1],
        date="2012-12-12",
        time="12:00",
    )
    s1 = from_source(
        "cds", "reanalysis-era5-single-levels", variable=variable1, **base_request
    )
    s2 = from_source(
        "cds", "reanalysis-era5-single-levels", variable=variable2, **base_request
    )
    assert s1.path == s2.path
    assert set(s1.to_xarray().data_vars) == expected_vars
    assert s1.to_xarray()["longitude"].values.tolist() == list(range(-50, 51, 2))
    assert s1.to_xarray()["latitude"].values.tolist() == list(range(50, 19, -1))


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.parametrize(
    "split_on,expected_len",
    (
        [None, 1],
        [[], 1],
        [{}, 1],
        ["variable", 2],
        [("variable",), 2],
        [{"variable": 1}, 2],
        [{"variable": 1, "time": 2}, 2],
        [{"variable": 2, "time": 1}, 2],
        [("variable", "time"), 4],
        [{"variable": 1, "time": 1}, 4],
    ),
)
def test_cds_split_on(split_on, expected_len):
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time=["00:00", "12:00"],
        split_on=split_on,
    )
    if expected_len == 1:
        assert hasattr(s, "path")
        assert not hasattr(s, "indexes")
    else:
        assert not hasattr(s, "path")
        assert len(s.indexes) == expected_len


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
@pytest.mark.parametrize(
    "split_on1,split_on2,expected_len",
    (
        [None, None, 2],
        [None, "time", 3],
        ["time", "time", 4],
    ),
)
def test_cds_multiple_requests(split_on1, split_on2, expected_len):
    base_request = dict(
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time=["00:00", "12:00"],
    )
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        base_request | {"variable": "2t", "split_on": split_on1},
        base_request | {"variable": "msl", "split_on": split_on2},
    )
    assert len(s.indexes) == expected_len


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_netcdf():
    s = from_source(
        "cds",
        "reanalysis-era5-single-levels",
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        format="netcdf",
    )
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_netcdf_selection_limited():
    s = from_source(
        "cds",
        "satellite-albedo",
        {
            "variable": "albb_bh",
            "satellite": "noaa_7",
            "sensor": "avhrr",
            "product_version": "v2",
            "horizontal_resolution": "4km",
            "year": "1983",
            "month": "01",
            "nominal_day": "10",
        },
    )
    assert len(s) == 9


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_observation_csv_file_to_pandas_xarray():
    collection_id = "insitu-observations-gruan-reference-network"
    request = {
        "format": "csv-lev.zip",
        "year": "2006",
        "month": "05",
        "variable": ["air_temperature", "altitude"],
        "day": ["21", "22"],
    }
    data_cds = from_source("cds", collection_id, **request)
    data_file = from_source("file", data_cds.path)
    assert "report_timestamp" in data_cds.to_pandas().columns

    # Assert consistent behaviour for local and CDS versions
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_non_observation_csv_file_to_pandas_xarray():
    collection_id = "sis-energy-derived-reanalysis"
    request = {
        "variable": "wind_power_generation_onshore",
        "spatial_aggregation": "country_level",
        "energy_product_type": "energy",
        "temporal_aggregation": "daily",
        "format": "zip",
    }
    data_cds = from_source("cds", collection_id, **request)
    assert "Date" in data_cds.to_pandas().columns

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_grib_to_pandas_xarray():
    collection_id = "reanalysis-era5-single-levels"
    request = dict(
        variable=["2t", "msl"],
        product_type="reanalysis",
        area=[50, -50, 20, 50],
        date="2012-12-12/to/2012-12-15",
        time="12:00",
    )
    data_cds = from_source("cds", collection_id, **request)

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_pandas().equals(data_file.to_pandas())
    assert data_cds.to_xarray().equals(data_file.to_xarray())


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CDS, reason="No access to CDS")
def test_cds_netcdf_to_pandas_xarray():
    collection_id = "satellite-methane"
    request = {
        "format": "zip",
        "processing_level": "level_2",
        "variable": "xch4",
        "sensor_and_algorithm": "merged_emma",
        "version": "4.4",
        "year": "2021",
        "month": "01",
        "day": "01",
    }

    data_cds = from_source("cds", collection_id, **request)
    assert "xch4" in data_cds.to_xarray().data_vars

    # Assert a consistent behviour for local and remote versions
    data_file = from_source("file", data_cds.path)
    assert data_cds.to_xarray().equals(data_file.to_xarray())
    # Implement to_dataframe
    # assert data_cds.to_pandas().equals(data_file.to_pandas())


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
