import pytest
from click.testing import CliRunner
from earthkit.cli.main import earthkit

from earthkit.cli.data import ls
from earthkit.data.utils.testing import earthkit_examples_file


def test_cli_ls_registered():
    assert earthkit.commands["ls"] is ls


@pytest.mark.parametrize(
    "arguments",
    [
        ["--keys", "parameter.variable,vertical.level"],
        ["--keys", "parameter.variable", "--keys", "vertical.level"],
    ],
)
def test_cli_ls_keys(arguments):
    result = CliRunner().invoke(ls, [earthkit_examples_file("tuv_pl.grib"), "--num", "2", *arguments])
    assert result.exit_code == 0, result.output
    header, *rows = result.output.splitlines()
    assert header.split() == ["parameter.variable", "vertical.level"]
    assert len(rows) == 2


def test_cli_ls_extra_keys():
    result = CliRunner().invoke(ls, [earthkit_examples_file("tuv_pl.grib"), "--extra-keys", "metadata.paramId"])
    assert result.exit_code == 0, result.output
    assert "metadata.paramId" in result.output.splitlines()[0]


def test_cli_ls_usage():
    result = CliRunner().invoke(earthkit, ["ls", "--help"])
    assert result.exit_code == 0
    assert "--keys" in result.output
    for flag in ("-k,", "-n,", "-e,"):
        assert flag not in result.output
