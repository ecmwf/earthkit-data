# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class FilePartStreamReader:
    def __init__(self, path, parts, chunk_size=1024 * 1024):
        self.path = path
        self.parts = parts
        self.chunk_size = chunk_size

    def __iter__(self):
        yield from self._iter_chunks()

    # TODO: use this method alternatively
    # def __iter_full_parts(self):
    #     with open(self.path, "rb") as f:
    #         for offset, length in self.parts:
    #             f.seek(offset)
    #             yield f.read(length)

    def _iter_chunks(self):
        with open(self.path, "rb") as f:
            for offset, length in self.parts:
                pos = offset
                size = length
                while size > 0:
                    f.seek(pos)
                    chunk = f.read(min(self.chunk_size, size))
                    if len(chunk) >= size:
                        yield chunk[:size]
                        size = -1
                    else:
                        yield chunk
                        size -= len(chunk)
                        pos += len(chunk)


class RequestIterStreamer:
    """Expose chunk-based stream reader as a stream supporting a generic read method."""

    def __init__(self, iter_content):
        from collections import deque

        self.iter_content = iter_content
        self.content = deque()
        self.position = 0
        self.total = 0
        self.consumed = False

    def _ensure_content(self, size):
        while self.total < size:
            try:
                self.content.append(next(self.iter_content))
                self.total += len(self.content[-1])
            except StopIteration:
                break

    def _read(self, size):
        assert len(self.content) > 0

        start = self.position
        length = min(len(self.content[0]) - start, size)
        end = start + length
        data = self.content[0][start:end]
        last = 0
        size -= length

        if size > 0:
            d = [data]
            for i in range(1, len(self.content)):
                start = 0
                length = min(len(self.content[i]) - start, size)
                end = start + length
                d.append(self.content[i][start:end])
                last = i
                size -= length
                if size <= 0:
                    break
            data = data = b"".join(d)

        return data, last, end, size

    def read(self, size=-1):
        if size < -1 or size == 0 or self.consumed:
            return bytes()

        if size == -1:
            return self.readall()

        self._ensure_content(size)
        if len(self.content) == 0 or self.total == 0:
            self.close()
            return bytes()

        data, last, self.position, missing_size = self._read(size)
        # LOG.debug(f"{size=} {last=} pos={self.position} {missing_size=}")
        if missing_size > 0:
            self.close()
        else:
            if self.position == len(self.content[last]):
                last += 1
                self.position = 0

            if last > 0:
                for _ in range(0, last):
                    self.content.popleft()

            self.total = sum(len(x) for x in self.content)
            self.total -= self.position

        return data

    def readall(self):
        if self.consumed:
            return bytes()

        first = self.read(self.total)
        if len(first) == 0:
            first = next(self.iter_content)
        res = [first]

        for d in self.iter_content:
            res.append(d)

        self.close()

        if len(res) == 1:
            return res[0]
        else:
            return b"".join(res)

    def peek(self, size):
        if size <= 0 or self.consumed:
            return bytes()

        self._ensure_content(size)
        data, _, _, _ = self._read(size)
        return data

    def close(self):
        if not self.closed:
            self._clear()

    @property
    def closed(self):
        return self.consumed

    def _clear(self):
        self.iter_content = None
        self.content.clear()
        self.position = 0
        self.consumed = True
