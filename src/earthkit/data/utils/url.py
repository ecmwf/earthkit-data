# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import copy
from collections import namedtuple

from earthkit.data.utils import ensure_sequence
from earthkit.data.utils.parts import PathAndParts

UrlSpecItem = namedtuple("UrlSpecItem", ["url", "parts", "kwargs"])


def parse_url_args(urls, **kwargs):
    urls = ensure_sequence(urls)
    res_url = []
    res_kwargs = []

    parts = kwargs.pop("parts", None)
    for url in urls:
        if isinstance(url, dict):
            u = url.pop("url")
            p = url.pop("parts", None)
            if p is not None:
                res_url.append([u, p])
            else:
                res_url.append(u)

            _kwarg = dict(**kwargs)
            _kwarg.update(url)
            res_kwargs.append(_kwarg)
        else:
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
    sequence = True


class UrlSpec:
    def __init__(self, spec, urls_and_parts):
        """Should not be instantiated directly.
        The public API are the factory methods."""
        self.spec = spec
        self.url_and_parts = urls_and_parts

    @classmethod
    def from_urls(cls, urls, **kwargs):
        spec = []
        if isinstance(urls, UrlSpecItem):
            spec.append(urls)
            url_and_parts = UrlSourcePathAndParts.from_paths(urls.url, urls.parts)
        else:
            url, _kwargs, parts_kwarg = parse_url_args(urls, **kwargs)
            url_and_parts = UrlSourcePathAndParts.from_paths(url, parts_kwarg)
            for i, x in enumerate(url_and_parts):
                spec.append(UrlSpecItem(x[0], x[1], _kwargs[i]))
        return cls(spec, url_and_parts)

    def __len__(self):
        return len(self.spec)

    def __iter__(self):
        return iter(self.spec)

    def __getitem__(self, n):
        return self.spec[n]

    @property
    def url(self):
        return self.url_and_parts.path

    @property
    def parts(self):
        return self.url_and_parts.parts

    def zipped(self):
        return self.url_and_parts.zipped()

    def sorted(self):
        spec = sorted(copy.deepcopy(self.spec), key=lambda spec: spec[0])
        url_and_parts = self.url_and_parts.sorted()
        return UrlSpec(spec, url_and_parts)
