import emohawk


def test_version() -> None:
    assert emohawk.__version__ != "999"
