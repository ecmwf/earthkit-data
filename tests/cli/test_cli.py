from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from earthkit.data import from_source
from earthkit.data.cli import COMMANDS, _selection_value, sel
from earthkit.data.utils.testing import earthkit_examples_file


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


@pytest.mark.parametrize("suffix", ["grib", "nc"])
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


def test_cli_sel_registered():
    assert COMMANDS["sel"] is sel
