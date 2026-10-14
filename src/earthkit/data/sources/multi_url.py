# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .multi import MultiSource


class MultiUrl(MultiSource):
    """MultiUrl source for downloading data from multiple URLs into a separate target file for each URL.

    This source is only used internally and cannot be used directly by end users via :func:`from_source`.
    """

    def __init__(self, urls, *args, filter=None, merger=None, force=None, lazily=True, sort_urls=False, **kwargs):
        from earthkit.data.utils.url import UrlSpec

        if isinstance(urls, UrlSpec):
            url_spec = urls
        else:
            url_spec = UrlSpec.from_urls(urls, **kwargs)

        assert len(url_spec) > 0

        if sort_urls:
            url_spec = url_spec.sorted()

        if lazily:
            # Load lazily so we can do parallel downloads
            from earthkit.data.sources import from_source_lazily

            sources = [from_source_lazily("url", x, filter=filter, merger=merger, force=force) for x in url_spec]
        else:
            from earthkit.data.sources.url import Url
            from earthkit.data.sources.utils import _mutate_source

            sources = [_mutate_source(Url(x, filter=filter, merger=merger, force=force)) for x in url_spec]

        super().__init__(sources, filter=filter, merger=merger)
