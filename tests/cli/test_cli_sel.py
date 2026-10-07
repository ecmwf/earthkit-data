import datetime
from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from earthkit.data import from_source
from earthkit.data.cli import COMMANDS, _selection_value, sel
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file


@pytest.mark.parametrize(
    "value,expected",
    [
        ("t", "t"),
        ("01400", "01400"),
        ("1,4", ["1", "4"]),
        (" t, u ", ["t", "u"]),
        ("1:4", [1, 2, 3]),
        ("1:6:2", [1, 3, 5]),
        ("4:1:-1", [4, 3, 2]),
        ("-2:1", [-2, -1, 0]),
        ("1:1", []),
        ("1:4,6", [1, 2, 3, "6"]),
    ],
)
def test_cli_selection_value(value, expected):
    assert _selection_value(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", " ", "1,", ",1", "1,,4", ":", "1:4:0", "1:4:2:3", "a:b", ":1,4", "4:,1", ":1:2", "4::2"],
)
def test_cli_selection_value_invalid(value):
    with pytest.raises(ValueError):
        _selection_value(value)


@pytest.mark.parametrize(
    "value,expected",
    [
        (":1", [True, True, False, False, False]),
        ("4:", [False, False, False, False, True]),
    ],
)
def test_cli_selection_value_unbound(value, expected):
    selection = _selection_value(value)
    assert [selection(number) for number in [-1, 0, 1, 3, 4]] == expected
    assert not selection(None)


@pytest.mark.parametrize("suffix", ["grib"])
@pytest.mark.parametrize(
    "conditions,selection,count",
    [
        (["parameter.variable=t"], {"parameter.variable": "t"}, 6),
        (["parameter.variable=t,u"], {"parameter.variable": ["t", "u"]}, 12),
        (["vertical.level=300,500"], {"vertical.level": [300, 500]}, 6),
        (["vertical.level=300:500"], {"vertical.level": [300, 400]}, 6),
        (["vertical.level=300:701:200"], {"vertical.level": [300, 500, 700]}, 9),
        (["vertical.level=:500"], {"vertical.level": [300, 400]}, 6),
        (["vertical.level=700:"], {"vertical.level": [700, 850, 1000]}, 9),
        (
            ["parameter.variable=t", "vertical.level=300:500"],
            {"parameter.variable": "t", "vertical.level": [300, 400]},
            2,
        ),
        (
            ["parameter.variable=u,v", "vertical.level=300:500"],
            {"parameter.variable": ["u", "v"], "vertical.level": [300, 400]},
            4,
        ),
    ],
)
def test_cli_sel_fields(tmp_path, suffix, conditions, selection, count):
    source = earthkit_examples_file(f"tuv_pl.{suffix}")
    target = tmp_path / f"selected.{suffix}"
    expected = from_source("file", source).to_fieldlist().sel(selection)
    assert len(expected) == count

    result = CliRunner().invoke(sel, [source, str(target), *conditions])
    assert result.exit_code == 0, result.output

    actual = from_source("file", str(target)).to_fieldlist()
    assert len(actual) == count
    keys = ["parameter.variable", "vertical.level"]
    expected_fields = {tuple(field.get(keys)): field.to_numpy() for field in expected}
    for field in actual:
        np.testing.assert_allclose(field.to_numpy(), expected_fields[tuple(field.get(keys))])


@pytest.mark.parametrize(
    "conditions,indexers",
    [
        (["level=700"], {"level": 700}),
        (["level=300,500"], {"level": [500, 300]}),
        (["level=300:500"], {"level": [400, 300]}),
        (["level=300:701:200"], {"level": [700, 500, 300]}),
        (["level=:500"], {"level": [400, 300]}),
        (["level=700:"], {"level": [1000, 850, 700]}),
        (["level=300:500", "latitude=0,30"], {"level": [400, 300], "latitude": [30, 0]}),
    ],
)
def test_cli_sel_netcdf(tmp_path, monkeypatch, conditions, indexers):
    import xarray as xr

    from earthkit.data.data.netcdf import NetCDFData

    def refuse_fieldlist(*args, **kwargs):
        pytest.fail("NetCDF selection must not convert to a FieldList")

    monkeypatch.setattr(NetCDFData, "to_fieldlist", refuse_fieldlist)
    source = earthkit_examples_file("tuv_pl.nc")
    target = tmp_path / "selected.nc"
    with xr.open_dataset(source) as dataset:
        expected = dataset.sel(indexers).load()

    result = CliRunner().invoke(sel, [source, str(target), *conditions])
    assert result.exit_code == 0, result.output
    with xr.open_dataset(target) as actual:
        xr.testing.assert_identical(actual, expected)


def test_cli_sel_netcdf_native_coordinates(tmp_path):
    import xarray as xr

    source = tmp_path / "input.data"
    target = tmp_path / "selected.nc"
    dataset = xr.Dataset(
        {"reading": (("station", "sample"), np.arange(12).reshape(2, 6))},
        coords={"station": ["north", "south"], "sample": np.arange(6)},
        attrs={"description": "Station observations"},
    )
    dataset.to_netcdf(source)
    result = CliRunner().invoke(sel, [str(source), str(target), "station=south", "sample=1:4"])
    assert result.exit_code == 0, result.output
    with xr.open_dataset(target) as actual:
        xr.testing.assert_identical(actual, dataset.sel(station="south", sample=[1, 2, 3]))


@pytest.mark.parametrize(
    "conditions,selection,count",
    [
        (["dataCategory=2"], {"dataCategory": 2}, 10),
        (["ident=01400,11747"], {"ident": ["01400", "11747"]}, 2),
        (["dataCategory=1:2"], {"dataCategory": [1]}, 0),
        (["dataCategory=2:3"], {"dataCategory": [2]}, 10),
        (["dataCategory=:2"], {"dataCategory": [0, 1]}, 0),
        (["dataCategory=:3"], {"dataCategory": [0, 1, 2]}, 10),
        (["dataCategory=2:"], {"dataCategory": [2]}, 10),
        (["dataCategory=4:"], {"dataCategory": [4]}, 0),
        (["dataCategory=2", "ident=01400"], {"dataCategory": 2, "ident": "01400"}, 1),
        (["ident=01400", "dataCategory=2:3"], {"ident": "01400", "dataCategory": [2]}, 1),
        (["ident=01400", "dataCategory=1:2"], {"ident": "01400", "dataCategory": [1]}, 0),
    ],
)
def test_cli_sel_bufr(tmp_path, conditions, selection, count):
    source = earthkit_examples_file("temp_10.bufr")
    target = tmp_path / "selected.bufr"
    expected = from_source("file", source).to_featurelist().sel(selection)
    assert len(expected) == count

    result = CliRunner().invoke(sel, [source, str(target), *conditions])
    assert result.exit_code == 0, result.output
    if count == 0:
        assert not target.exists() or target.stat().st_size == 0
    else:
        actual = from_source("file", str(target)).to_featurelist()
        assert len(actual) == count
        assert actual.metadata(["dataCategory", "ident"]) == expected.metadata(["dataCategory", "ident"])


@pytest.mark.parametrize("conditions", [[], ["param"], ["=t"], ["param="], ["param=t", "param=u"], ["level=1:4:0"]])
def test_cli_sel_invalid_conditions(tmp_path, conditions):
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(sel, [earthkit_examples_file("tuv_pl.grib"), str(target), *conditions])
    assert result.exit_code == 2
    assert not target.exists()


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_cli_sel_refuses_input_overwrite(tmp_path, alias):
    source = tmp_path / "source.grib"
    original = Path(earthkit_examples_file("tuv_pl.grib")).read_bytes()
    source.write_bytes(original)
    target = source
    if alias != "same":
        target = tmp_path / "target.grib"
        if alias == "symlink":
            target.symlink_to(source)
        else:
            target.hardlink_to(source)
    result = CliRunner().invoke(sel, [str(source), str(target), "parameter.variable=t"])
    assert result.exit_code == 1
    assert "Source and target files must be different" in result.output
    assert source.read_bytes() == original


def _check_grib_selection(tmp_path, source, conditions, keys, expected_metadata):
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(sel, [source, str(target), *conditions])
    assert result.exit_code == 0, result.output
    if not expected_metadata:
        assert not target.exists() or target.stat().st_size == 0
        return

    actual = from_source("file", str(target)).to_fieldlist()
    assert len(actual) == len(expected_metadata)
    assert actual.get(keys) == expected_metadata
    original = from_source("file", source).to_fieldlist()
    expected_fields = [field for field in original if field.get(keys) in expected_metadata]
    for field, expected in zip(actual, expected_fields):
        np.testing.assert_array_equal(field.to_numpy(), expected.to_numpy())


@pytest.mark.parametrize("key", ["parameter.variable", "metadata.shortName"])
def test_cli_sel_grib_single_message(tmp_path, key):
    _check_grib_selection(tmp_path, earthkit_test_data_file("test_single.grib"), [f"{key}=2t"], [key], [["2t"]])


@pytest.mark.parametrize(
    "conditions,keys,expected_metadata",
    [
        (["parameter.variable=u", "vertical.level=700"], ["parameter.variable", "vertical.level"], [["u", 700]]),
        (["metadata.paramId=131", "vertical.level=700"], ["metadata.paramId", "vertical.level"], [[131, 700]]),
        (
            ["parameter.variable=t,u", "vertical.level=700,500"],
            ["parameter.variable", "vertical.level"],
            [["t", 700], ["u", 700], ["t", 500], ["u", 500]],
        ),
        (["variable=w"], ["variable"], []),
        (["INVALIDKEY=w"], ["INVALIDKEY"], []),
        (
            ["parameter.variable=t", "vertical.level=500,700", "metadata.marsType=an"],
            ["parameter.variable", "vertical.level", "metadata.marsType"],
            [["t", 700, "an"], ["t", 500, "an"]],
        ),
        (
            ["parameter.variable=t", "vertical.level=500,700", "metadata.mars.type=an"],
            ["parameter.variable", "vertical.level", "metadata.mars.type"],
            [["t", 700, "an"], ["t", 500, "an"]],
        ),
    ],
)
def test_cli_sel_grib_single_file(tmp_path, conditions, keys, expected_metadata):
    _check_grib_selection(tmp_path, earthkit_examples_file("tuv_pl.grib"), conditions, keys, expected_metadata)


@pytest.mark.parametrize(
    "level,expected_metadata",
    [
        ("600:701", [[131, 700]]),
        ("650:751", [[131, 700]]),
        ("1000:", [[131, 1000]]),
        (":301", [[131, 300]]),
        ("500:701", [[131, 700], [131, 500]]),
        ("510:521", []),
    ],
)
def test_cli_sel_grib_slice_single_file(tmp_path, level, expected_metadata):
    _check_grib_selection(
        tmp_path,
        earthkit_examples_file("tuv_pl.grib"),
        ["metadata.paramId=131", f"vertical.level={level}"],
        ["metadata.paramId", "vertical.level"],
        expected_metadata,
    )


def test_cli_sel_grib_time_steps_repeated(tmp_path):
    for _ in range(2):
        _check_grib_selection(
            tmp_path,
            earthkit_test_data_file("t_time_series.grib"),
            ["parameter.variable=t", "time.step=3,6"],
            ["parameter.variable", "vertical.level", "time.step"],
            [["t", 1000, datetime.timedelta(hours=3)], ["t", 1000, datetime.timedelta(hours=6)]],
        )


@pytest.mark.parametrize("step_key", ["metadata.endStep", "metadata.step", "time.step"])
def test_cli_sel_grib_date_time_step(tmp_path, step_key):
    _check_grib_selection(
        tmp_path,
        earthkit_test_data_file("t_time_series.grib"),
        ["metadata.date=20201221", "metadata.time=1200", f"{step_key}=9"],
        ["metadata.shortName", "metadata.date", "metadata.time", "metadata.step", "time.step"],
        [
            ["t", 20201221, 1200, 9, datetime.timedelta(hours=9)],
            ["z", 20201221, 1200, 9, datetime.timedelta(hours=9)],
        ],
    )


def test_cli_sel_grib_valid_datetime(tmp_path):
    _check_grib_selection(
        tmp_path,
        earthkit_test_data_file("t_time_series.grib"),
        ["time.valid_datetime=2020-12-21T21:00:00"],
        ["parameter.variable", "time.base_datetime", "time.step"],
        [
            ["t", datetime.datetime(2020, 12, 21, 12), datetime.timedelta(hours=9)],
            ["z", datetime.datetime(2020, 12, 21, 12), datetime.timedelta(hours=9)],
        ],
    )


@pytest.mark.parametrize("key", ["time.base_datetime", "time.forecast_reference_time"])
def test_cli_sel_grib_base_datetime(tmp_path, key):
    _check_grib_selection(
        tmp_path,
        earthkit_test_data_file("t_time_series.grib"),
        [f"{key}=2020-12-21T12:00:00"],
        ["parameter.variable", "time.base_datetime", "time.step"],
        [
            [variable, datetime.datetime(2020, 12, 21, 12), datetime.timedelta(hours=step)]
            for step in [0, 3, 6, 9, 48]
            for variable in ["t", "z"]
        ],
    )


def test_cli_sel_registered():
    assert COMMANDS["sel"] is sel
