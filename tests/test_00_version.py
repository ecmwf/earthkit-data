import earthkit.data


def test_version() -> None:
    assert earthkit.data.__version__ != "999"
