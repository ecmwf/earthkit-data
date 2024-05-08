# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from .file import FileSource

LOG = logging.getLogger(__name__)


REMOTE_SAMPLE_DATA_URL = "https://get.ecmwf.int/repository/earthkit/samples/"


class Sample(FileSource):
    def __init__(self, path, *args, **kwargs):
        super().__init__()

        self._paths = path
        if isinstance(self._paths, str):
            self._paths = [path]

        self._kwargs = dict(**kwargs)

    def mutate(self):
        from earthkit.data.sources.url import Url

        urls = []
        for f_name in self._paths:
            urls.append(REMOTE_SAMPLE_DATA_URL + f_name)

        return Url(urls, **self._kwargs)


source = Sample
