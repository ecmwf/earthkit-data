# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import subprocess

from earthkit.data.core.settings import SETTINGS
from earthkit.data.core.temporary import temp_file

from .file import FileSource

LOG = logging.getLogger(__name__)


class StandaloneMarsClient:
    def __init__(self, log="default"):
        self.log = log

    def execute(self, request, target, log=None):
        req = ["retrieve,"]

        for k, v in request.items():
            if isinstance(v, (list, tuple)):
                v = "/".join([str(x) for x in v])
            req += [f"{k}={v},"]

        req += [f'target="{target}"']
        req_str = "\n".join(req)
        with temp_file() as filename:
            with open(filename, "w") as f:
                f.write(req_str + "\n")
            LOG.debug(f"Sending Mars request: '{req_str}'")

            log = {}
            if self.log is None:
                log = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            elif self.log and isinstance(self.log, dict):
                log = self.log
            elif self.log != "default":
                raise ValueError(f"Unsupported log type={type(self.log)}")

            subprocess.run(
                [self.command(), filename],
                env=dict(os.environ, MARS_AUTO_SPLIT_BY_DATES="1"),
                check=True,
                **log,
            )

    @staticmethod
    def command():
        return os.environ.get("MARS_CLIENT_COMMAND", "/usr/local/bin/mars")

    @staticmethod
    def enabled():
        return SETTINGS.get("use-standalone-mars-client-when-available") and os.path.exists(
            StandaloneMarsClient.command()
        )


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
