# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.sources.multi_url import MultiUrl
from earthkit.data.sources.stream import StreamSource

from .file import FileSource

LOG = logging.getLogger(__name__)


def bucket_to_url(bucket, key):
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def request_to_url(requests):
    urls = []
    for r in requests:
        bucket = r["bucket"]
        for obj in r["objects"]:
            url = bucket_to_url(bucket, obj["object"])
            urls.append(url)
    return urls


class S3Source(FileSource):
    def __init__(self, *args, stream=True, **kwargs) -> None:
        super().__init__()

        self._stream_kwargs = dict()
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = {}
        for a in args:
            self.request.update(a)
        self.request.update(kwargs)

        if not isinstance(self.request, list):
            self.request = [self.request]

        self.urls = request_to_url(self.request)

    def mutate(self):
        if self.stream:
            from urllib.request import urlopen

            # TODO: the stream has to be closed
            if len(self.urls) == 1:
                stream = urlopen(self.urls[0])
                return StreamSource(stream, **self._stream_kwargs)
            else:
                assert False
        else:
            return S3FileSource(self.urls)

    def __repr__(self) -> str:
        return self.__class__.__name__


class S3FileSource(FileSource):
    def __init__(self, urls):
        super().__init__()
        self.urls = urls

    def mutate(self):
        return MultiUrl(self.urls)


source = S3Source
