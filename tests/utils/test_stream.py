# Test RequestIterStreamer object from sources/url.py

#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data.utils.stream import RequestIterStreamer


def iter_stream(chunk_size, data):
    num = len(data)
    pos = 0
    while pos < num:
        start = pos
        end = min(pos + chunk_size, num)
        pos += end - start
        yield data[start:end]


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 4, 5, 10, 12, 14])
@pytest.mark.parametrize("read_size", [1, 2, 3, 4, 5, 10, 12, 14])
def test_request_iter_streamer(chunk_size, read_size):
    data = str.encode("0123456789abc")

    stream = RequestIterStreamer(iter_stream(chunk_size, data))

    assert not stream.closed
    assert stream.read(-2) == bytes()
    assert stream.read(0) == bytes()
    assert stream.peek(4) == data[:4]
    assert not stream.closed

    for i in range(0, len(data), read_size):
        assert stream.read(read_size) == data[i : min(i + read_size, len(data))], i

    assert stream.read(1) == bytes()
    assert stream.closed
    assert stream.read(0) == bytes()
    assert stream.read() == bytes()
    assert stream.read(-1) == bytes()
    assert stream.peek(4) == bytes()


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 4, 5, 10, 12, 14])
def test_request_iter_streamer_read_all_1(chunk_size):
    data = str.encode("0123456789abc")

    stream = RequestIterStreamer(iter_stream(chunk_size, data))

    assert not stream.closed
    assert stream.read(-2) == bytes()
    assert stream.read(0) == bytes()
    assert stream.peek(4) == data[:4]
    assert not stream.closed

    assert stream.read() == data

    assert stream.read(1) == bytes()
    assert stream.closed
    assert stream.read(0) == bytes()
    assert stream.read(-1) == bytes()
    assert stream.peek(4) == bytes()


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 4, 5, 10, 12, 14])
def test_request_iter_streamer_read_all_2(chunk_size):
    data = str.encode("0123456789abc")

    stream = RequestIterStreamer(iter_stream(chunk_size, data))

    assert not stream.closed
    assert stream.read() == data

    assert stream.read(1) == bytes()
    assert stream.closed
    assert stream.read(0) == bytes()
    assert stream.read(-1) == bytes()
    assert stream.peek(4) == bytes()


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
