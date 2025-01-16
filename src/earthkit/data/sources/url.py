# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

from multiurl import Downloader

from earthkit.data.core.caching import cache_file
from earthkit.data.core.config import CONFIG
from earthkit.data.core.statistics import record_statistics
from earthkit.data.utils.parts import PathAndParts
from earthkit.data.utils.progbar import progress_bar

from .file import FileSource

LOG = logging.getLogger(__name__)


def _ignore(*args, **kwargs):
    pass


SCHEME_TO_SOURCE = {"ec:": "ecfs", "ecfs:": "ecfs"}


def download_and_cache(
    url,
    *,
    owner="url",
    parts=None,
    verify=True,
    force=None,
    chunk_size=1024 * 1024,
    range_method="auto",
    http_headers=None,
    update_if_out_of_date=False,
    fake_headers=None,  # When HEAD is not allowed but you know the size
    **kwargs,
):
    # TODO: re-enable this feature
    extension = None

    LOG.debug("URL %s", url)

    downloader = Downloader(
        url,
        chunk_size=chunk_size,
        timeout=CONFIG.get("url-download-timeout"),
        verify=verify,
        parts=parts,
        range_method=range_method,
        http_headers=http_headers,
        fake_headers=fake_headers,
        statistics_gatherer=record_statistics,
        progress_bar=progress_bar,
        resume_transfers=True,
        override_target_file=False,
        download_file_extension=".download",
    )

    if extension and extension[0] != ".":
        extension = "." + extension

    if extension is None:
        extension = downloader.extension()

    path = downloader.local_path()
    if path is not None:
        return

    def out_of_date(url, path, cache_data):
        if CONFIG.get("check-out-of-date-urls") is False:
            return False

        if downloader.out_of_date(path, cache_data):
            if CONFIG.get("download-out-of-date-urls") or update_if_out_of_date:
                LOG.warning(
                    "Invalidating cache version and re-downloading %s",
                    url,
                )
                return True
            else:
                LOG.warning(
                    "To enable automatic downloading of updated URLs set the 'download-out-of-date-urls'"
                    " setting to True",
                )
        return False

    if force is None:
        force = out_of_date

    def download(target, _):
        downloader.download(target)
        return downloader.cache_data()

    path = cache_file(
        owner,
        download,
        dict(url=url, parts=parts),
        extension=extension,
        force=force,
    )

    return path


class UrlSourcePathAndParts(PathAndParts):
    compress = True


class UrlBase(FileSource):
    def __init__(
        self,
        url,
        chunk_size=1024 * 1024,
        parts=None,
        filter=None,
        merger=None,
        verify=True,
        range_method="auto",
        http_headers=None,
        fake_headers=None,  # When HEAD is not allowed but you know the size
        stream=False,
        auth=None,
        **kwargs,
    ):
        super().__init__(filter=filter, merger=merger)

        from earthkit.data.utils.url import UrlSpec
        from earthkit.data.utils.url import UrlSpecItem

        if isinstance(url, UrlSpecItem):
            self.url_spec = UrlSpec.from_urls(url)
        else:
            url_kwargs = dict(
                chunk_size=chunk_size,
                parts=parts,
                verify=verify,
                range_method=range_method,
                http_headers=http_headers,
                fake_headers=fake_headers,
                auth=auth,
            )
            self.url_spec = UrlSpec.from_urls(url, **url_kwargs)

        self._kwargs = kwargs
        LOG.debug(f"url={self.url} url_parts={self.url_parts} auth={auth} _kwargs={self._kwargs}")

    def connect_to_mirror(self, mirror):
        return mirror.connection_for_url(self, self.url, self.url_parts)

    def prepare_headers(self, url):
        headers = {}
        if self.http_headers is not None:
            headers = dict(self.http_headers)

        if self.auth is not None:
            headers.update(self.auth.auth_header(url))

        if not headers:
            headers = None

        return headers

    @property
    def url(self):
        return self.url_spec.url

    @property
    def url_parts(self):
        return self.url_spec.parts

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.url})"


class Url(UrlBase):
    """Represent a URL source.

    Parameters
    ----------
    url: str, list, tuple, UrlSpecItem, dict or an iterable of these
        A single ``url`` can be:

        * a str
        * a list/tuple of two items. The first item is the url as a str, while the second
          item defines the parts for the given url. In this case the ``parts`` kwargs
          cannot be used.
        * a UrlSpecItem
        * a dict with same content as UrlSpecItem. Mandatory key is "url" and optionally
          "parts" and "kwargs" can be used.

        Multiple urls can be provided as a list/tuple of of the single url formats above.
        Mixing single url formats in a list/tuple is not allowed.
    """

    def __init__(
        self,
        url,
        *,
        update_if_out_of_date=False,
        force=None,
        stream=False,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        self.other_source = None

        if isinstance(url, str):
            for scheme, source in SCHEME_TO_SOURCE.items():
                if url.startswith(scheme):
                    self.other_source = (source, url, kwargs)
                    return

        self.update_if_out_of_date = update_if_out_of_date
        self.force = force
        self.stream = stream

        if not self.stream:
            self._download()

    def mutate(self):

        if self.other_source:
            from earthkit.data import from_source

            source, url, kwargs = self.other_source
            return from_source(source, url, **kwargs)

        if self.stream:
            s = []
            # create one stream source per url
            for x in self.url_spec:
                s.append(SingleUrlStream(x))

            from .stream import make_stream_source_from_other

            return make_stream_source_from_other(s, **self._kwargs)

        return super().mutate()

    def _download(self):
        # TODO: re-enable this feature
        extension = None

        LOG.debug(
            (
                f"url={self.url} url_parts={self.url_parts} "
                # f"http_headers={self.http_headers}"
                f" _kwargs={self._kwargs}"
            )
        )

        self.downloader = Downloader(
            self.url_spec.zipped(),
            timeout=CONFIG.get("url-download-timeout"),
            statistics_gatherer=record_statistics,
            progress_bar=progress_bar,
            resume_transfers=True,
            override_target_file=False,
            download_file_extension=".download",
            **self.url_spec[0].kwargs,
        )

        if extension and extension[0] != ".":
            extension = "." + extension

        if extension is None:
            extension = self.downloader.extension()

        self.path = self.downloader.local_path()
        if self.path is not None:
            return

        if self.force is None:
            self.force = self.out_of_date

        def download(target, _):
            self.downloader.download(target)
            return self.downloader.cache_data()

        self.path = self.cache_file(
            download,
            dict(url=self.url, parts=self.url_parts),
            extension=extension,
            force=self.force,
        )

        # cache data may contain the result of the http HEAD request
        h = self.downloader.cache_data()
        if isinstance(h, dict):
            self.content_type = h.get("content-type")

    def out_of_date(self, url, path, cache_data):
        if CONFIG.get("check-out-of-date-urls") is False:
            return False

        if self.downloader.out_of_date(path, cache_data):
            if CONFIG.get("download-out-of-date-urls") or self.update_if_out_of_date:
                LOG.warning(
                    "Invalidating cache version and re-downloading %s",
                    self.url,
                )
                return True
            else:
                LOG.warning(
                    "To enable automatic downloading of updated URLs set the 'download-out-of-date-urls'"
                    " setting to True",
                )
        return False


class SingleUrlStream(UrlBase):
    def __init__(
        self,
        url,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        if len(self.url_spec) != 1:
            raise TypeError("Only a single url is supported")

        assert isinstance(self.url[0], str)

        from urllib.parse import urlparse

        assert isinstance(self.url, (list, tuple)), f"{self.url=}"
        o = urlparse(self.url[0])
        if o.scheme not in ("http", "https"):
            raise NotImplementedError(f"Streams are not supported for scheme={o.scheme} urls")

    def mutate(self):
        from .stream import _from_source

        return _from_source(self, **self._kwargs)

    def to_stream(self):
        from earthkit.data.utils.stream import RequestIterStreamer

        downloader = Downloader(
            self.url_spec.zipped(),
            timeout=CONFIG.get("url-download-timeout"),
            # verify=self.verify,
            # range_method=self.range_method,
            # http_headers=self.prepare_headers(self.url),
            # fake_headers=self.fake_headers,
            statistics_gatherer=_ignore,
            progress_bar=progress_bar,
            resume_transfers=False,
            override_target_file=False,
            **self.url_spec[0].kwargs,
        )

        _, _, _, _ = downloader.estimate_size(None)

        # cache data may contain the result of the http HEAD request
        h = downloader.cache_data()
        if isinstance(h, dict):
            self.content_type = h.get("content-type")

        stream = downloader.make_stream()
        return RequestIterStreamer(stream(chunk_size=self.url_spec[0].kwargs["chunk_size"]))


source = Url
