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
from earthkit.data.utils import ensure_sequence

from .file import FileSource

LOG = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "s3.amazonaws.com"
DEFAULT_REGION = "eu-west-2"


def request_to_resource(requests):
    def _make_part(offset, length):
        if offset is not None:
            offset = int(offset)

        if length is not None:
            length = int(length)

        if offset is not None or length is not None:
            return [(offset, length)]

    resources = []
    for r in requests:
        bucket = r["bucket"]
        endpoint = r.get("endpoint", DEFAULT_ENDPOINT)
        o = ensure_sequence(r["objects"])
        for obj in o:
            if isinstance(obj, str):
                key = obj
                resources.append(S3Resource(endpoint, bucket, key))
            else:
                key = obj["object"]
                region = obj.ge("region", DEFAULT_REGION)
                parts = obj.get("parts", None)
                resources.append(S3Resource(endpoint, bucket, region, key, parts=parts))
    return resources


class S3Authenticator:
    def __init__(self, region):
        self.region = region

    @staticmethod
    def _host(url):
        from urllib.parse import urlparse

        return urlparse(url).netloc

    def __call__(self, r):
        from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

        host = self._host(r.url)
        auth = BotoAWSRequestsAuth(
            aws_host=host,
            aws_region=self.region,
            aws_service="s3",
        )

        # BotoAWSRequestsAuth raises AttributeError when no credentials are found
        # because it wants to call a method on a None object. Until this is handled
        # correctly in aws_requests_auth we raise a properly worded exception.
        try:
            return auth(r)
        except AttributeError:
            raise Exception(
                (
                    "No S3 credentials were found using botocore. See the following page "
                    "about how credentials are searched for: http://boto3.readthedocs.io/en/"
                    "latest/guide/configuration.html#configuring-credentials"
                )
            ) from None


class S3Resource:
    def __init__(self, endpoint, bucket, region, key, parts=None):
        self.endpoint = endpoint
        self.region = region
        self.bucket = bucket
        self.key = key
        self.parts = parts

    @property
    def url(self):
        if "amazonaws" in self.endpoint:
            return f"https://{self.bucket}.{self.endpoint}/{self.key}"
        else:
            return f"https://{self.endpoint}/{self.bucket}/{self.key}"

    def host(self):
        if "amazonaws" in self.endpoint:
            return f"{self.bucket}.{self.endpoint}"
        else:
            return f"{self.endpoint}"

    def __repr__(self):
        return f"{self.__class__.__name__}(url={self.url}, part={self.part})"


class S3Source(FileSource):
    """Represent an AWS S3 bucket source"""

    def __init__(self, *args, anon=True, stream=False, **kwargs) -> None:
        super().__init__()

        self.anon = anon

        self._stream_kwargs = dict()
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = []
        for a in args:
            self.request.append(a)
        # self.request.update(kwargs)

        # if not isinstance(self.request, list):
        #     self.request = [self.request]

        self.resources = request_to_resource(self.request)

    def mutate(self):
        if self.stream:
            urls = []
            has_parts = any(r.parts is not None for r in self.resources)

            if has_parts:
                for r in self.resources:
                    urls.append([r.url, r.parts])
            else:
                for r in self.resources:
                    urls.append(r.url)

            if not self.anon and has_parts:
                fake_headers = {"accept-ranges": "bytes"}
            else:
                fake_headers = None

            auth = self.make_auth()

            if self.stream:
                return Url(
                    urls,
                    auth=auth,
                    fake_headers=fake_headers,
                    stream=True,
                    **self._stream_kwargs,
                )
        else:
            url_spec = []
            has_parts = any(r.parts is not None for r in self.resources)
            for r in self.resources:
                r = {"url": r.url}
                if has_parts:
                    r["parts"] = r.parts
                if not self.anon:
                    auth = S3Authenticator(r.region)
                    r["auth"] = auth
                url_spec.append(r)

            if not self.anon and has_parts:
                fake_headers = {"accept-ranges": "bytes"}
            else:
                fake_headers = None

            return MultiUrl(url_spec, fake_headers=fake_headers)

        # urls  = []
        # has_parts = any(r.parts is not None for r in self.resources)
        # if not self.anon else None

        # if has_parts:
        #     for r in self.resources:
        #         urls.append([r.url, r.parts])
        # else:
        #     for r in self.resources:
        #         urls.append(r.url)

        # if not self.anon and has_parts:
        #     fake_headers = {"accept-ranges": "bytes"}
        # else:
        #     fake_headers = None

        # auth = self.make_auth(len(urls))

        # if self.stream:
        #     return Url(
        #         urls,
        #         auth=auth,
        #         fake_headers=fake_headers,
        #         stream=True,
        #         **self._stream_kwargs,
        #     )

        # else:
        #     return MultiUrl(urls, fake_headers=fake_headers, auth=auth)

    def make_auth(self):
        return S3Authenticator() if not self.anon else None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


source = S3Source
