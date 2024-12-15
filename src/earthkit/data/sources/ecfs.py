# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import subprocess

from .file import FileSource

LOG = logging.getLogger(__name__)


class ECFSRetriever(FileSource):
    def __init__(
        self,
        url,
        *,
        force=False,
        **kwargs,
    ):
        super().__init__(url, **kwargs)

        self.path = self.cache_file(
            self._fetch,
            url,
            force=force,
        )

    def _fetch(self, target, url):
        if not url.startswith("ec:"):
            url = f"ec:{url}"

        LOG.debug("%s", f"Fetching {url} to {target}")

        subprocess.run(["ecp", url, target], check=True)


source = ECFSRetriever
