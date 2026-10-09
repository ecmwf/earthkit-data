from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner
from earthkit.cli.main import earthkit

from earthkit.cli.data import order_by
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file


def _keys(arguments):
    """Turn KEY[=ORDER] arguments into -k options."""
    return [option for argument in arguments for option in ("-k", argument)]


@pytest.mark.parametrize(
    "arguments,ordering",
    [
        (["parameter.variable"], {"parameter.variable": "ascending"}),
        (["parameter.variable=ascending"], {"parameter.variable": "ascending"}),
        (["parameter.variable=descending"], {"parameter.variable": "descending"}),
        (
            ["vertical.level", "parameter.variable"],
            {"vertical.level": "ascending", "parameter.variable": "ascending"},
        ),
        (
            ["parameter.variable=ascending", "vertical.level=descending"],
            {"parameter.variable": "ascending", "vertical.level": "descending"},
        ),
        (["parameter.variable=u,t,v"], {"parameter.variable": ["u", "t", "v"]}),
        (
            ["vertical.level=700,300,1000,400,850,500", "parameter.variable=v,u,t"],
            {"vertical.level": [700, 300, 1000, 400, 850, 500], "parameter.variable": ["v", "u", "t"]},
        ),
        ([" parameter.variable = u, t, v "], {"parameter.variable": ["u", "t", "v"]}),
    ],
)
def test_cli_order_by_grib(tmp_path, arguments, ordering):
    source = earthkit_examples_file("tuv_pl.grib")
    target = tmp_path / "ordered.grib"
    original = from_source("file", source).to_fieldlist()
    expected = original.order_by(ordering)

    result = CliRunner().invoke(order_by, [source, str(target), *_keys(arguments)])
    assert result.exit_code == 0, result.output
    actual = from_source("file", str(target)).to_fieldlist()
    assert len(actual) == len(original)
    assert actual.get(["parameter.variable", "vertical.level"]) == expected.get([
        "parameter.variable",
        "vertical.level",
    ])
    for field, reference in zip(actual, expected):
        np.testing.assert_array_equal(field.to_numpy(), reference.to_numpy())


@pytest.mark.parametrize("direction", ["ascending", "descending", "custom"])
def test_cli_order_by_bufr(tmp_path, direction):
    identifiers = ["01001", "01152", "01241", "01400", "01415", "02836", "02963", "03953", "11035", "11747"]
    if direction == "ascending":
        arguments = ["ident"]
    elif direction == "descending":
        identifiers.reverse()
        arguments = ["dataCategory", "ident=descending"]
    else:
        identifiers = identifiers[3:] + identifiers[:3]
        arguments = [f"ident={','.join(identifiers)}"]

    source = earthkit_examples_file("temp_10.bufr")
    target = tmp_path / "ordered.bufr"
    result = CliRunner().invoke(order_by, [source, str(target), *_keys(arguments)])
    assert result.exit_code == 0, result.output
    actual = from_source("file", str(target)).to_featurelist()
    assert len(actual) == 10
    assert actual.metadata("ident") == identifiers
    assert actual.metadata("dataCategory") == [2] * 10


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["=ascending"],
        [" "],
        ["parameter.variable="],
        ["parameter.variable=asc"],
        ["parameter.variable=t,"],
        ["parameter.variable=t,,u"],
        ["parameter.variable=t,t,u"],
        ["parameter.variable", "parameter.variable=descending"],
    ],
)
def test_cli_order_by_invalid_arguments(tmp_path, arguments):
    target = tmp_path / "ordered.grib"
    result = CliRunner().invoke(order_by, [earthkit_examples_file("tuv_pl.grib"), str(target), *_keys(arguments)])
    assert result.exit_code == 2
    assert not target.exists()


def test_cli_order_by_incomplete_custom_order(tmp_path):
    target = tmp_path / "ordered.grib"
    result = CliRunner().invoke(
        order_by, [earthkit_examples_file("tuv_pl.grib"), str(target), "-k", "parameter.variable=t,u"]
    )
    assert result.exit_code == 1
    assert "Could not order" in result.output
    assert not target.exists()


@pytest.mark.parametrize("format_name", ["netcdf", "text"])
def test_cli_order_by_unsupported_format(tmp_path, format_name):
    source = tmp_path / "input.data"
    if format_name == "netcdf":
        source.write_bytes(Path(earthkit_examples_file("tuv_pl.nc")).read_bytes())
    else:
        source.write_text("Unsupported ordering input\n")
    target = tmp_path / "ordered.grib"
    result = CliRunner().invoke(order_by, [str(source), str(target), "--key", "vertical.level"])
    assert result.exit_code == 1
    assert "only supports GRIB and BUFR input" in result.output
    assert not target.exists()


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_cli_order_by_refuses_input_overwrite(tmp_path, alias):
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
    result = CliRunner().invoke(order_by, [str(source), str(target), "--key", "parameter.variable"])
    assert result.exit_code == 1
    assert "Source and target files must be different" in result.output
    assert source.read_bytes() == original


def test_cli_order_by_registered():
    assert earthkit.commands["order_by"] is order_by


def test_cli_order_by_stdin_stdout():
    source = Path(earthkit_examples_file("tuv_pl.grib")).read_bytes()
    result = CliRunner().invoke(order_by, ["-", "-", "-k", "vertical.level=descending"], input=source)
    assert result.exit_code == 0, result.output
    ordered = from_source("memory", result.stdout_bytes).to_fieldlist()
    assert ordered.get("vertical.level")[::3] == [1000, 850, 700, 500, 400, 300]


def test_cli_order_by_usage():
    result = CliRunner().invoke(earthkit, ["order_by", "--help"])
    assert result.exit_code == 0
    assert "[OPTIONS] SOURCE TARGET" in result.output
    assert "-k, --key KEY[=ORDER]" in result.output
