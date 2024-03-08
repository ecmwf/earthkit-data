# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from collections import namedtuple

from earthkit.data.utils import ensure_sequence
from earthkit.data.utils.parts import PathAndParts

UrlSpecItem = namedtuple("UrlSpecItem", ["url", "parts", "kwargs"])


def parse_url_args(urls, **kwargs):
    urls = ensure_sequence(urls)
    res_url = []
    res_kwargs = []

    parts = None
    for url in urls:
        if isinstance(url, dict):
            u = url.pop("url")
            if "parts" in url:
                p = url.pop("parts")
                res_url.append([u, p])
            else:
                res_url.append(u)

            _kwarg = dict(**kwargs)
            _kwarg.update(url)
            p = _kwarg.pop("parts", None)
            if p is not None:
                parts = p
            res_kwargs.append(_kwarg)
        else:
            # if isinstance(url, str):
            #     key = url
            # elif isinstance(url, (list, tuple)):
            #     key = url[0]

            p = kwargs.pop("parts", None)
            if p is not None:
                parts = p

            res_url.append(url)
            res_kwargs.append(kwargs)

    # if len(res) > 1:
    #     res = sorted(res, key=lambda x: x["key"])
    return res_url, res_kwargs, parts


class UrlSourcePathAndParts(PathAndParts):
    compress = True
    sequence = False


class UrlSpec:
    def __init__(self, urls, **kwargs):
        print(f"CONSTRUCTOR {urls=}")
        self.spec = []

        if isinstance(urls, UrlSpecItem):
            self.spec.append(urls)
            self.url_and_parts = PathAndParts(urls.url, urls.parts)

            # url, parts_kwarg, self.kwargs = urls.url, urls.parts, urls.kwargs
        else:
            url, _kwargs, parts_kwarg = parse_url_args(urls, **kwargs)
            self.url_and_parts = PathAndParts(url, parts_kwarg)

            self.spec = []
            for i, x in enumerate(self.url_and_parts):
                self.spec.append(UrlSpecItem(x[0], x[1], _kwargs[i]))

        # self.single = isinstance(self.url_and_parts.path, str)
        # if self.single:
        #     if isinstance(self.kwargs, list):
        #         self.kwargs = self.kwargs[0]

        # print(
        #     f"   -> single={self.single} kwargs={self.kwargs} url={self.url} parts={self.parts}"
        # )

    # specs = None
    # parts_kwarg = None
    # _paths_and_parts = None

    # def from_args(urls, **kwargs):
    #     s = UrlSpec()
    #     s.specs, s.parts_kwarg = parse_url_args(urls, **kwargs)

    # def from_spec(specs):
    #     s = UrlSpec()
    #     s.specs = ensure_sequence(specs)
    #     return s

    def __len__(self):
        return len(self.spec)

    def __iter__(self):
        return iter(self.spec)

    #     n = 1 if self.single else len(self.url)
    #     print(f"LEN={n}")
    #     return n

    def __getitem__(self, n):
        return self.spec[n]

    # def __getitem__(self, n):
    #     print(f"getItem {n=}")
    #     if self.single:
    #         if n == 0:
    #             return UrlSpecItem(
    #                 self.url_and_parts.path,
    #                 self.url_and_parts.parts,
    #                 self.kwargs,
    #             )

    #     else:
    #         return UrlSpecItem(
    #             self.url_and_parts.path[n],
    #             self.url_and_parts.parts[n],
    #             self.kwargs[n],
    #         )

    @property
    def url(self):
        return self.url_and_parts.path

    @property
    def parts(self):
        return self.url_and_parts.parts

    def zipped(self):
        return self.url_and_parts.zipped()

    # def __next__(self):
    #     return UrlSpec.from_spec

    # @property
    # def paths_and_parts(self):
    #     if self._paths_and_parts is None:
    #         u = [x["url"] for x in self.spec]
    #         self._paths_and_parts = UrlSourcePathAndParts(u, self.parts_kwarg)
    #     return self._paths_and_parts
