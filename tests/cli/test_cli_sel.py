import datetime
from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner
from earthkit.cli.main import earthkit

from earthkit.cli.data import _selection_value, sel
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file


@pytest.mark.parametrize(
    "value,expected",
    [
        ("t", "t"),
        ("01400", "01400"),
        ('"2t"', "2t"),
        ("1,4", ["1", "4"]),
        (" t, u ", ["t", "u"]),
        ('"x,y",z', ["x,y", "z"]),
        # Slices include their stop
        ("1:4", slice(1, 4)),
        ("-2:1", slice(-2, 1)),
        ("1:1", slice(1, 1)),
        (":500", slice(None, 500)),
        ("700:", slice(700, None)),
        ("0.5:1.5", slice(0.5, 1.5)),
        ("2000:2001", slice(2000, 2001)),
        ('"2000":"2001"', slice("2000", "2001")),
        ('"a":', slice("a", None)),
        (
            "2020-12-21T00:00:2020-12-22T00:00",
            slice(datetime.datetime(2020, 12, 21), datetime.datetime(2020, 12, 22)),
        ),
        ("2020-12-21:2020-12-22", slice(datetime.datetime(2020, 12, 21), datetime.datetime(2020, 12, 22))),
        # A single ISO date-time is a scalar, not a slice
        ("2020-12-21T21:00:00", "2020-12-21T21:00:00"),
        # A step, or a list, expands integer slices to the values they include
        ("1:6:2", [1, 3, 5]),
        ("300:700:200", [300, 500, 700]),
        ("4:1:-1", [4, 3, 2, 1]),
        ("1:4,6", [1, 2, 3, 4, "6"]),
    ],
)
def test_cli_selection_value(value, expected):
    assert _selection_value(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "1,",
        ",1",
        "1,,4",
        ":",
        "1:4:0",
        "1:4:2:3",
        "a:b",
        ":1,4",
        "4:,1",
        ":1:2",
        "4::2",
        '1:"a"',
        "0.5:1.5:1",
        "2020-12-21:2020-12-22:1",
    ],
)
def test_cli_selection_value_invalid(value):
    with pytest.raises(ValueError):
        _selection_value(value)


def _options(conditions):
    """Turn KEY=VALUE conditions into --KEY=VALUE options."""
    return [f"--{condition}" for condition in conditions]


@pytest.mark.parametrize("suffix", ["grib"])
@pytest.mark.parametrize(
    "conditions,selection,count",
    [
        (["parameter.variable=t"], {"parameter.variable": "t"}, 6),
        (["parameter.variable=t,u"], {"parameter.variable": ["t", "u"]}, 12),
        (["vertical.level=300,500"], {"vertical.level": [300, 500]}, 6),
        (["vertical.level=300:500"], {"vertical.level": [300, 400, 500]}, 9),
        (["vertical.level=300:700:200"], {"vertical.level": [300, 500, 700]}, 9),
        (["vertical.level=:500"], {"vertical.level": [300, 400, 500]}, 9),
        (["vertical.level=700:"], {"vertical.level": [700, 850, 1000]}, 9),
        (['parameter.variable="t":"u"'], {"parameter.variable": ["t", "u"]}, 12),
        (
            ["parameter.variable=t", "vertical.level=300:500"],
            {"parameter.variable": "t", "vertical.level": [300, 400, 500]},
            3,
        ),
        (
            ["parameter.variable=u,v", "vertical.level=300:500"],
            {"parameter.variable": ["u", "v"], "vertical.level": [300, 400, 500]},
            6,
        ),
    ],
)
def test_cli_sel_fields(tmp_path, suffix, conditions, selection, count):
    source = earthkit_examples_file(f"tuv_pl.{suffix}")
    target = tmp_path / f"selected.{suffix}"
    expected = from_source("file", source).to_fieldlist().sel(selection)
    assert len(expected) == count

    result = CliRunner().invoke(sel, [source, str(target), *_options(conditions)])
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
        (["level=300:500"], {"level": [500, 400, 300]}),
        (["level=300:700:200"], {"level": [700, 500, 300]}),
        (["level=:500"], {"level": [500, 400, 300]}),
        (["level=700:"], {"level": [1000, 850, 700]}),
        (["level=500:300"], {"level": [500, 400, 300]}),
        (["level=300:500", "latitude=0,30"], {"level": [500, 400, 300], "latitude": [30, 0]}),
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

    result = CliRunner().invoke(sel, [source, str(target), *_options(conditions)])
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
    result = CliRunner().invoke(sel, [str(source), str(target), "--station", "south", "--sample", "1:4"])
    assert result.exit_code == 0, result.output
    with xr.open_dataset(target) as actual:
        xr.testing.assert_identical(actual, dataset.sel(station="south", sample=[1, 2, 3, 4]))


@pytest.mark.parametrize(
    "conditions,selection,count",
    [
        (["dataCategory=2"], {"dataCategory": 2}, 10),
        (["ident=01400,11747"], {"ident": ["01400", "11747"]}, 2),
        (["dataCategory=0:1"], {"dataCategory": [0, 1]}, 0),
        (["dataCategory=1:2"], {"dataCategory": [1, 2]}, 10),
        (["dataCategory=2:3"], {"dataCategory": [2, 3]}, 10),
        (["dataCategory=:1"], {"dataCategory": [0, 1]}, 0),
        (["dataCategory=:2"], {"dataCategory": [0, 1, 2]}, 10),
        (["dataCategory=2:"], {"dataCategory": [2]}, 10),
        (["dataCategory=3:"], {"dataCategory": [3]}, 0),
        (["dataCategory=2", "ident=01400"], {"dataCategory": 2, "ident": "01400"}, 1),
        (["ident=01400", "dataCategory=2:3"], {"ident": "01400", "dataCategory": [2]}, 1),
        (["ident=01400", "dataCategory=0:1"], {"ident": "01400", "dataCategory": [1]}, 0),
    ],
)
def test_cli_sel_bufr(tmp_path, conditions, selection, count):
    source = earthkit_examples_file("temp_10.bufr")
    target = tmp_path / "selected.bufr"
    expected = from_source("file", source).to_featurelist().sel(selection)
    assert len(expected) == count

    result = CliRunner().invoke(sel, [source, str(target), *_options(conditions)])
    assert result.exit_code == 0, result.output
    if count == 0:
        assert not target.exists() or target.stat().st_size == 0
    else:
        actual = from_source("file", str(target)).to_featurelist()
        assert len(actual) == count
        assert actual.metadata(["dataCategory", "ident"]) == expected.metadata(["dataCategory", "ident"])


@pytest.mark.parametrize(
    "conditions,message",
    [
        ([], "At least one --KEY VALUE condition is required"),
        (["--param"], "Option '--param' requires a value"),
        (["--=t"], "No such option"),
        (["--param="], "Selection values must not be empty"),
        (["--param", "t", "--param=u"], "Duplicate selection key 'param'"),
        (["--level", "1:4:0"], "Invalid value for '--level'"),
        (["--level", "a:b"], "Slices must be START:STOP[:STEP]"),
    ],
)
def test_cli_sel_invalid_conditions(tmp_path, conditions, message):
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(sel, [earthkit_examples_file("tuv_pl.grib"), str(target), *conditions])
    assert result.exit_code == 2, result.output
    assert message in result.output
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
    result = CliRunner().invoke(sel, [str(source), str(target), "--parameter.variable", "t"])
    assert result.exit_code == 1
    assert "Source and target files must be different" in result.output
    assert source.read_bytes() == original


def _check_grib_selection(tmp_path, source, conditions, keys, expected_metadata):
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(sel, [source, str(target), *_options(conditions)])
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
        ("600:700", [[131, 700]]),
        ("650:750", [[131, 700]]),
        ("1000:", [[131, 1000]]),
        (":300", [[131, 300]]),
        ("500:700", [[131, 700], [131, 500]]),
        ("700:500", [[131, 700], [131, 500]]),
        ("510:520", []),
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
    assert earthkit.commands["sel"] is sel


def test_cli_sel_grib_valid_datetime_slice(tmp_path):
    _check_grib_selection(
        tmp_path,
        earthkit_test_data_file("t_time_series.grib"),
        ["time.valid_datetime=2020-12-21T12:00:2020-12-21T18:00"],
        ["parameter.variable", "time.base_datetime", "time.step"],
        [
            [variable, datetime.datetime(2020, 12, 21, 12), datetime.timedelta(hours=step)]
            for step in [0, 3, 6]
            for variable in ["t", "z"]
        ],
    )


@pytest.mark.parametrize(
    "arguments",
    [
        ["SOURCE", "TARGET", "--metadata.paramId", "131", "--vertical.level", "500:700"],
        ["SOURCE", "TARGET", "--metadata.paramId=131", "--vertical.level=500:700"],
        ["--metadata.paramId", "131", "SOURCE", "--vertical.level", "500:700", "TARGET"],
    ],
)
def test_cli_sel_condition_forms(tmp_path, arguments):
    target = tmp_path / "selected.grib"
    source = earthkit_examples_file("tuv_pl.grib")
    arguments = [{"SOURCE": source, "TARGET": str(target)}.get(a, a) for a in arguments]
    result = CliRunner().invoke(sel, arguments)
    assert result.exit_code == 0, result.output
    assert from_source("file", str(target)).to_fieldlist().get(["metadata.paramId", "vertical.level"]) == [
        [131, 700],
        [131, 500],
    ]


def test_cli_sel_merges_sources(tmp_path):
    source = earthkit_examples_file("tuv_pl.grib")
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(
        sel, [source, source, str(target), "--parameter.variable", "t", "--vertical.level", "500"]
    )
    assert result.exit_code == 0, result.output
    assert len(from_source("file", str(target)).to_fieldlist()) == 2


def test_cli_sel_stdin_stdout():
    source = Path(earthkit_examples_file("tuv_pl.grib")).read_bytes()
    result = CliRunner().invoke(sel, ["-", "-", "--metadata.paramId", "131"], input=source)
    assert result.exit_code == 0, result.output
    selected = from_source("memory", result.stdout_bytes).to_fieldlist()
    assert selected.get("metadata.paramId") == [131] * 6


def test_cli_sel_usage():
    result = CliRunner().invoke(earthkit, ["sel", "--help"])
    assert result.exit_code == 0
    assert "[OPTIONS] SOURCE TARGET --KEY VALUE [--KEY VALUE]..." in result.output
