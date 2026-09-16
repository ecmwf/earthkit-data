from struct import pack, pack_into

import numpy as np

from earthkit.data import from_source


def test_pcraster_reader(tmp_path):
    path = tmp_path / "data.map"
    expected = np.array([[1, -2147483648], [3, 4]], dtype=np.int32)

    # Source: https://github.com/pcraster/rasterformat, csf_format_v2.pdf, Appendix A.
    # CSF v2 stores its main header at 0, raster header at 64, and row-major data at 256.
    header = bytearray(256)
    pack_into("=32sHIHIHI", header, 0, b"RUU CROSS SYSTEM MAP FORMAT", 2, 0, 1, 0, 1, 1)
    pack_into("=HH8s8sddIIddd", header, 64, 0xE2, 0x26, pack("=i", 1), pack("=i", 4), 0, 0, *expected.shape, 1, 1, 0)
    path.write_bytes(header + expected.tobytes())

    data = from_source("file", path)
    np.testing.assert_equal(data.to_numpy(), [[1, np.nan], [3, 4]])
    np.testing.assert_array_equal(data.to_numpy(mask=False), expected)
