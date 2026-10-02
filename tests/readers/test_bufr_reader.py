import pytest

import earthkit.data as ekd


def test_invalid_kwargs():
    with pytest.warns(UserWarning):
        ekd.from_source("sample", "temp_10.bufr", grib_handle_policy=None)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
