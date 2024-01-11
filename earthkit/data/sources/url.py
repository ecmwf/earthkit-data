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
from earthkit.data.core.settings import SETTINGS
from earthkit.data.core.statistics import record_statistics
from earthkit.data.utils import progress_bar

from .file import FileSource

LOG = logging.getLogger(__name__)


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
        timeout=SETTINGS.get("url-download-timeout"),
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
        if SETTINGS.get("check-out-of-date-urls") is False:
            return False

        if downloader.out_of_date(path, cache_data):
            if SETTINGS.get("download-out-of-date-urls") or update_if_out_of_date:
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


class UrlBase(FileSource):
    def __init__(
        self,
        url,
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

        self.url = url
        self.parts = parts
        self.http_headers = http_headers
        self.auth = auth
        self.verify = verify
        self.range_method = range_method
        self.fake_headers = fake_headers
        self.stream = stream
        self._kwargs = kwargs
        LOG.debug(
            f"url={self.url} parts={self.parts} auth={self.auth} _kwargs={self._kwargs}"
        )

    def connect_to_mirror(self, mirror):
        return mirror.connection_for_url(self, self.url, self.parts)

    def prepare_headers(self, url):
        headers = {}
        if self.http_headers is not None:
            headers = dict(self.http_headers)

        if self.auth is not None:
            headers.update(self.auth.auth_header(url))

        if not headers:
            headers = None

        return headers

    def _get_parts(self, url):
        if isinstance(self.parts, dict):
            return self.parts.get(url, None)
        else:
            return self.parts

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.url})"


class Url(UrlBase):
    """Represent a URL source.

    Parameters
    ----------
    url: str, list, tuple
        Single url or a list/tuple of urls. A url item can be:

        * a str
        * a list/tuple of two items. The first item is the url as a str, while the second
          item defines the parts for the given url. In this case the ``parts`` kwargs
          cannot be used.

        When ``url`` is a list/tuple these two formats cannot be mixed so either all the url
        items are str or a list/tuple of url and parts.

    """

    def __init__(
        self,
        url,
        *,
        chunk_size=1024 * 1024,
        update_if_out_of_date=False,
        force=None,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        # TODO: re-enable this feature
        extension = None

        if not self.stream:
            self.update_if_out_of_date = update_if_out_of_date

            # ensure no parts kwargs is used when the parts are defined together with the urls
            _parts_kwargs = {}
            if not isinstance(url, (list, tuple)):
                url = [url]
            if isinstance(url[0], (list, tuple)):
                if self.parts is not None:
                    raise ValueError("cannot specify parts both as arg and kwarg")
            else:
                _parts_kwargs = {"parts": self.parts}

            LOG.debug(f"http_headers={self.http_headers}")

            self.downloader = Downloader(
                self.url,
                chunk_size=chunk_size,
                timeout=SETTINGS.get("url-download-timeout"),
                verify=self.verify,
                range_method=self.range_method,
                http_headers=self.prepare_headers(self.url),
                fake_headers=self.fake_headers,
                statistics_gatherer=record_statistics,
                progress_bar=progress_bar,
                resume_transfers=True,
                override_target_file=False,
                download_file_extension=".download",
                **_parts_kwargs,
            )

            if extension and extension[0] != ".":
                extension = "." + extension

            if extension is None:
                extension = self.downloader.extension()

            self.path = self.downloader.local_path()
            if self.path is not None:
                return

            if force is None:
                force = self.out_of_date

            def download(target, _):
                self.downloader.download(target)
                return self.downloader.cache_data()

            self.path = self.cache_file(
                download,
                dict(url=self.url, parts=self.parts),
                extension=extension,
                force=force,
            )

    def mutate(self):
        if self.stream:
            # create one stream source per url
            from multiurl.downloader import _canonicalize

            s = []
            _kwargs = {}
            if self.parts is not None:
                _kwargs = {"parts": self.parts}
            urls, _ = _canonicalize(self.url, **_kwargs)

            for url, parts in urls:
                s.append(
                    SingleUrlStream(
                        url,
                        parts=parts,
                        verify=True,
                        range_method="auto",
                        http_headers=self.prepare_headers(url),
                        fake_headers=None,
                        auth=self.auth,
                    )
                )

            from .stream import _from_source

            return _from_source(s, **self._kwargs)
        else:
            return super().mutate()

    def out_of_date(self, url, path, cache_data):
        if SETTINGS.get("check-out-of-date-urls") is False:
            return False

        if self.downloader.out_of_date(path, cache_data):
            if SETTINGS.get("download-out-of-date-urls") or self.update_if_out_of_date:
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

        if isinstance(self.url, (list, tuple)):
            raise TypeError("only a single url is supported")

    def mutate(self):
        from .stream import _from_source

        return _from_source(self, **self._kwargs)

    def to_stream(self):
        from urllib.request import Request, urlopen

        headers = self.prepare_headers(self.url)

        # TODO: ensure stream is closed when consumed
        # TODO: use multiurl
        r = Request(self.url, headers=headers)
        return urlopen(r)

    def prepare_headers(self, url):
        headers = super().prepare_headers(url)
        parts = self.parts_header(self.parts)
        if parts is not None and parts:
            if headers is None:
                headers = {}
            headers.update(parts)
        return headers if headers is not None else {}

    def parts_header(self, parts):
        if parts is not None:
            if isinstance(parts, (list, tuple)):
                part = parts[0]
            else:
                part = parts

            offset, length = part.offset, part.length
            if offset is None:
                offset = 0

            start = offset
            end = ""

            if length is not None:
                end = offset + length - 1

            return {"Range": f"bytes={start}-{end}"}
        else:
            return {}


source = Url
