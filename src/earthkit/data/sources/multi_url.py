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

# from earthkit.data.utils import ensure_sequence


# def _parse_urls(urls, **kwargs):
#     urls = ensure_sequence(urls)
#     res = []
#     for url in urls:
#         if isinstance(url, dict):
#             u = url.pop("url")
#             r = {"_key": u}
#             if "parts" in url:
#                 p = url.pop("parts")
#                 r["url"] = [u, p]
#             else:
#                 r["url"] = u

#             _kwarg = dict(**kwargs)
#             _kwarg.update(url)
#             r["kwargs"] = _kwarg
#         else:
#             if isinstance(url, str):
#                 key = url
#             elif isinstance(url, (list, tuple)):
#                 key = url[0]
#             r = {"_key": key, "url": url, "kwargs": kwargs}
#         res.append(r)

#     # if len(res) > 1:
#     #     res = sorted(res, key=lambda x: x["key"])
#     return res


class MultiUrl(MultiSource):
    def __init__(
        self, urls, *args, filter=None, merger=None, force=None, lazily=True, **kwargs
    ):
        from earthkit.data.utils.url import UrlSpec

        if isinstance(urls, UrlSpec):
            url_spec = urls
        else:
            url_spec = UrlSpec(urls, **kwargs)

        assert len(url_spec) > 0

        # if not isinstance(urls, (list, tuple)):
        #     urls = [urls]

        # # if filter is not None:
        # #     urls = [url for url in urls if filter(url)]

        # assert len(urls)

        # # if len(urls) > 1 and isinstance(urls[0], str):
        #     urls = sorted(urls, key)

        sources = [
            from_source(
                "url",
                x,
                # x["url"],
                filter=filter,
                merger=merger,
                force=force,
                # Load lazily so we can do parallel downloads
                lazily=lazily,
                parallel=False,
                # **x["kwargs"]
            )
            for x in url_spec
        ]

        super().__init__(sources, filter=filter, merger=merger)
