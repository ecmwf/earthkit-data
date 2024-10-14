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


def request_to_resource(requests, global_credentials):
    resources = []
    for r in requests:
        bucket = r["bucket"]
        endpoint = r.get("endpoint", DEFAULT_ENDPOINT)
        o = ensure_sequence(r["objects"])
        credentials = S3Credentials.from_other(global_credentials)
        credentials.update(r)
        credentials.check()
        for obj in o:
            if isinstance(obj, str):
                key = obj
                resources.append(S3Resource(endpoint, bucket, DEFAULT_REGION, key))
            else:
                key = obj["object"]
                region = obj.get("region", DEFAULT_REGION)
                parts = obj.get("parts", None)
                resources.append(
                    S3Resource(
                        endpoint,
                        bucket,
                        region,
                        key,
                        parts=parts,
                        credentials=credentials,
                    )
                )

    return resources


class S3Credentials:
    def __init__(self, aws_access_key, aws_secret_access_key, aws_token=None):
        self.aws_access_key = aws_access_key
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_token = aws_token

    def check(self):
        if self.aws_access_key and not self.aws_secret_access_key:
            raise ValueError("When aws_access_key is provided, aws_secret_access_key must also be provided")

        if not self.aws_access_key and self.aws_secret_access_key:
            raise ValueError("When aws_secret_access_key is provided, aws_access_key must also be provided")

    @classmethod
    def from_other(self, other):
        if other is None:
            return self(None, None)
        return self(*[other.aws_access_key, other.aws_secret_access_key, other.aws_token])

    def valid(self):
        return self.aws_access_key and self.aws_secret_access_key

    def update(self, obj):
        self.aws_access_key = self.aws_access_key or obj.get("aws_access_key", None)
        self.aws_secret_access_key = self.aws_secret_access_key or obj.get("aws_secret_access_key", None)
        self.aws_token = self.aws_token or obj.get("aws_token", None)


class S3Authenticator:
    def __init__(self, region, credentials=None):
        self.region = region
        self.credentials = credentials

    @staticmethod
    def _host(url):
        from urllib.parse import urlparse

        return urlparse(url).netloc

    def __call__(self, r):
        if self.credentials is not None and self.credentials.valid():
            return self._base_auth(r)

        return self._boto_auth(r)

    def _base_auth(self, r):
        assert self.credentials is not None
        assert self.credentials.valid()
        from aws_requests_auth import AWSRequestsAuth

        host = self._host(r.url)
        auth = AWSRequestsAuth(
            aws_access_key=self.credentials.aws_access_key,
            aws_secret_access_key=self.credentials.aws_secret_access_key,
            aws_host=host,
            aws_region=self.region,
            aws_service="s3",
            aws_token=self.credentials.aws_token,
        )
        return auth(r)

    def _boto_auth(self, r):
        from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

        host = self._host(r.url)
        auth = BotoAWSRequestsAuth(
            aws_host=host,
            aws_region=self.region,
            aws_service="s3",
        )

        # BotoAWSRequestsAuth raises AttributeError when no credentials are found
        # due to calling a method on a None object. Until this is handled
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
    def __init__(self, endpoint, bucket, region, key, parts=None, credentials=None):
        self.endpoint = endpoint
        self.region = region
        self.bucket = bucket
        self.key = key
        self.parts = parts
        self.credentials = credentials

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

    def __init__(
        self,
        *args,
        stream=False,
        read_all=False,
        anon=True,
        aws_access_key=None,
        aws_secret_access_key=None,
        aws_token=None,
        **kwargs,
    ) -> None:
        super().__init__()

        self.anon = anon

        self.stream = stream
        self._stream_kwargs = dict(read_all=read_all)

        def _collect(r):
            if isinstance(r, dict):
                self.request.append(r)
            elif isinstance(r, (list, tuple)):
                for x in r:
                    _collect(x)
            else:
                raise ValueError(f"Invalid request: {r}")

        self.request = []
        for a in args:
            _collect(a)

        self.credentials = S3Credentials(aws_access_key, aws_secret_access_key, aws_token)
        self.resources = request_to_resource(self.request, self.credentials)

    def mutate(self):
        url_spec = []
        has_parts = any(r.parts is not None for r in self.resources)
        for r in self.resources:
            spec = {"url": r.url}
            if has_parts:
                spec["parts"] = r.parts
            if not self.anon:
                auth = S3Authenticator(r.region, credentials=r.credentials)
                spec["auth"] = auth
            url_spec.append(spec)

        if not self.anon and has_parts:
            fake_headers = {"accept-ranges": "bytes"}
        else:
            fake_headers = None

        if self.stream:
            return Url(
                url_spec,
                fake_headers=fake_headers,
                stream=True,
                **self._stream_kwargs,
            )
        else:
            return MultiUrl(url_spec, sort_urls=False, fake_headers=fake_headers)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


source = S3Source
