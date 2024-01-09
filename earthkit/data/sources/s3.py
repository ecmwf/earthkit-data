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
from earthkit.data.sources.url import Url
from earthkit.data.utils.url import UrlResource

from .file import FileSource

LOG = logging.getLogger(__name__)


def request_to_resource(requests, anon):
    resources = []
    for r in requests:
        bucket = r["bucket"]
        for obj in r["objects"]:
            key = obj["object"]
            resources.append(S3Resource(bucket, key, anon))
    return resources


class S3Resource(UrlResource):
    def __init__(self, bucket, key, anon):
        super().__init__(anon)
        self.bucket = bucket
        self.key = key

    @property
    def url(self):
        return f"https://{self.bucket}.s3.amazonaws.com/{self.key}"

    def _host(self):
        return f"{self.bucket}.s3.amazonaws.com"

    def auth(self):
        if not self.anon:
            from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

            class _R:
                def __init__(self, url):
                    self.method = "GET"
                    self.url = url
                    self.body = ""

            req = _R(self.url)

            auth = BotoAWSRequestsAuth(
                aws_host=self._host(),
                aws_region="eu-west-2",
                aws_service="s3",
            )

            return auth.get_aws_request_headers_handler(req)
        else:
            return {}


class S3Source(FileSource):
    def __init__(self, *args, anon=True, stream=True, **kwargs) -> None:
        super().__init__()

        self.anon = anon

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

        self.resources = request_to_resource(self.request, self.anon)

    def mutate(self):
        if self.stream:
            return Url(self.resources, stream=True, **self._stream_kwargs)
        else:
            return MultiUrl(self.resources)

    def __repr__(self) -> str:
        return self.__class__.__name__


source = S3Source
