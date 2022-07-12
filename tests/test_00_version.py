import teal


def test_version() -> None:
    assert teal.__version__ != "999"
