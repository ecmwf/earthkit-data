# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class UrlResource(metaclass=ABCMeta):
    def __init__(self, anon):
        self.anon = anon

    @property
    @abstractmethod
    def url(self):
        pass

    def auth(self):
        return {}

    def to_stream(self):
        from urllib.request import Request, urlopen

        headers = self.auth()

        # TODO: ensure stream is closed when consumed
        print(f"SELF={self.url}")
        r = Request(self.url, headers=headers)
        return urlopen(r)


class AnonymousUrlResource(UrlResource):
    def __init__(self, url):
        super().__init__(True)
        self._url = url

    @property
    def url(self):
        return self._url

    def auth(self):
        return {}
