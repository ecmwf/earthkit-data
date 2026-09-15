import numpy as np

from earthkit.data import from_source


def test_numpy_reader(tmp_path):
    path = tmp_path / "data.npy"
    expected = np.array([[1, 2], [3, 4]])
    np.save(path, expected)

    np.testing.assert_array_equal(from_source("file", path).to_numpy(), expected)


def test_numpy_zip_reader(tmp_path):
    path = tmp_path / "data.npz"
    expected = np.array([[1, 2], [3, 4]])
    np.savez(path, data=expected)

    with from_source("file", path).to_numpy() as result:
        np.testing.assert_array_equal(result["data"], expected)
