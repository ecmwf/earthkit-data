# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source

from .multi import MultiSource


class MultiUrl(MultiSource):
    def __init__(
        self, urls, *args, filter=None, merger=None, force=None, lazily=True, sort_urls=False, **kwargs
    ):
        from earthkit.data.utils.url import UrlSpec

        if isinstance(urls, UrlSpec):
            url_spec = urls
        else:
            url_spec = UrlSpec.from_urls(urls, **kwargs)

        assert len(url_spec) > 0

        if sort_urls:
            url_spec = url_spec.sorted()

        sources = [
            from_source(
                "url",
                x,
                filter=filter,
                merger=merger,
                force=force,
                # Load lazily so we can do parallel downloads
                lazily=lazily,
                # **x["kwargs"]
            )
            for x in url_spec
        ]

        super().__init__(sources, filter=filter, merger=merger)
