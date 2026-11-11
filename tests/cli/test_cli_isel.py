# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest
from click.testing import CliRunner
from earthkit.cli.main import earthkit

from earthkit.cli.data import isel
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file

KEYS = ["parameter.variable", "vertical.level"]


def test_cli_isel_registered():
    assert earthkit.commands["isel"] is isel


@pytest.mark.parametrize(
    "arguments,levels,variables",
    [
        # tuv_pl.grib has levels 300, 400, 500, 700, 850, 1000 and variables t, u, v
        (["--vertical.level", "0"], [300], ["t", "u", "v"]),
        (["--vertical.level", "-1"], [1000], ["t", "u", "v"]),
        (["--vertical.level", "1:3"], [400, 500], ["t", "u", "v"]),
        (["--vertical.level", "::2"], [300, 500, 850], ["t", "u", "v"]),
        (["--vertical.level", "0,5"], [300, 1000], ["t", "u", "v"]),
        (["--vertical.level=-2:", "--parameter.variable", "0,2"], [850, 1000], ["t", "v"]),
    ],
)
def test_cli_isel_grib(tmp_path, arguments, levels, variables):
    target = tmp_path / "selected.grib"
    result = CliRunner().invoke(isel, [earthkit_examples_file("tuv_pl.grib"), str(target), *arguments])
    assert result.exit_code == 0, result.output

    actual = from_source("file", str(target)).to_fieldlist()
    assert sorted({tuple(field.get(KEYS)) for field in actual}) == sorted(
        (variable, level) for variable in variables for level in levels
    )


def test_cli_isel_bufr(tmp_path):
    source = earthkit_examples_file("temp_10.bufr")
    target = tmp_path / "selected.bufr"
    idents = from_source("file", source).to_featurelist().unique("ident", sort=True, unwrap_single=True)

    result = CliRunner().invoke(isel, [source, str(target), "--ident", "0:2"])
    assert result.exit_code == 0, result.output
    actual = from_source("file", str(target)).to_featurelist()
    assert sorted(actual.unique("ident", unwrap_single=True)) == list(idents[0:2])


@pytest.mark.parametrize(
    "arguments,indexers",
    [
        (["--level", "0"], {"level": 0}),
        (["--level", "-1"], {"level": -1}),
        (["--level", "1:3"], {"level": slice(1, 3)}),
        (["--level", "0,2"], {"level": [0, 2]}),
        (["--level", "::2", "--latitude", "0"], {"level": slice(None, None, 2), "latitude": 0}),
    ],
)
def test_cli_isel_netcdf(tmp_path, arguments, indexers):
    import xarray as xr

    source = earthkit_examples_file("tuv_pl.nc")
    target = tmp_path / "selected.nc"
    with xr.open_dataset(source) as dataset:
        expected = dataset.isel(indexers).load()

    result = CliRunner().invoke(isel, [source, str(target), *arguments])
    assert result.exit_code == 0, result.output
    with xr.open_dataset(target) as actual:
        xr.testing.assert_identical(actual, expected)


def test_cli_isel_stdin_stdout():
    with open(earthkit_examples_file("tuv_pl.grib"), "rb") as f:
        data = f.read()
    result = CliRunner().invoke(isel, ["-", "-", "--vertical.level", "-1"], input=data)
    assert result.exit_code == 0, result.output

    actual = from_source("memory", result.stdout_bytes).to_fieldlist()
    assert set(actual.get("vertical.level")) == {1000}
    assert len(actual) == 3


@pytest.mark.parametrize(
    "source,arguments,message",
    [
        ("tuv_pl.grib", [], "At least one --KEY INDEX condition is required"),
        ("tuv_pl.grib", ["--vertical.level", "6"], "Index 6 is out of range for 6 values"),
        ("tuv_pl.grib", ["--vertical.level", "0,-7"], "Index -7 is out of range for 6 values"),
        ("tuv_pl.grib", ["--vertical.level", "4:2"], "The index selects no values"),
        ("tuv_pl.grib", ["--vertical.level", "a"], "Invalid value for '--vertical.level'"),
        ("tuv_pl.grib", ["--vertical.level", "1.5"], "Invalid value for '--vertical.level'"),
        ("tuv_pl.grib", ["--unknown.key", "0"], "No values found for metadata key 'unknown.key'"),
        ("tuv_pl.grib", ["--vertical.level", "0", "--vertical.level", "1"], "Duplicate selection key"),
        ("tuv_pl.nc", ["--lev", "0"], "'lev' is not a dimension"),
        ("tuv_pl.nc", ["--level", "10"], "Index 10 is out of range for 6 values"),
    ],
)
def test_cli_isel_invalid(tmp_path, source, arguments, message):
    target = tmp_path / ("selected." + source.rsplit(".", 1)[1])
    result = CliRunner().invoke(isel, [earthkit_examples_file(source), str(target), *arguments])
    assert result.exit_code == 2, result.output
    assert message in result.output


def test_cli_isel_same_file(tmp_path):
    import shutil

    source = tmp_path / "data.grib"
    shutil.copy(earthkit_examples_file("tuv_pl.grib"), source)
    result = CliRunner().invoke(isel, [str(source), str(source), "--vertical.level", "0"])
    assert result.exit_code == 1
    assert "Source and target files must be different" in result.output


def test_cli_isel_usage():
    result = CliRunner().invoke(earthkit, ["isel", "--help"])
    assert result.exit_code == 0
    assert "SOURCE TARGET --KEY INDEX [--KEY INDEX]..." in result.output
