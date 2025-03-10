# (C) Copyright 2020 ECMWF.
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

from earthkit.data.core.config import CONFIG
from earthkit.data.core.temporary import temp_file

from .ecmwf_api import ECMWFApi
from .ecmwf_api import MARSAPIKeyPrompt

LOG = logging.getLogger(__name__)


def _no_log(msg):
    pass


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
        return CONFIG.get("use-standalone-mars-client-when-available") and os.path.exists(
            StandaloneMarsClient.command()
        )


class MarsRetriever(ECMWFApi):
    def service(self):
        if StandaloneMarsClient.enabled():
            return StandaloneMarsClient(self.log)

        kwargs = {}
        if self.log is None:
            kwargs = {"log": _no_log}
        elif callable(self.log):
            kwargs = {"log": self.log}
        elif self.log != "default":
            raise ValueError(f"Unsupported log type={type(self.log)}")

        try:
            import ecmwfapi
        except ImportError:
            raise ImportError("MARS access requires 'ecmwf-api-client' to be installed")

        if self.prompt:
            prompt = MARSAPIKeyPrompt()
            prompt.check()

            try:
                return ecmwfapi.ECMWFService("mars", **kwargs)
            except Exception as e:
                if ".ecmwfapirc" in str(e) or not self.prompt.has_config_env():
                    LOG.warning(e)
                    LOG.exception(f"Could not load ecmwf api (mars) client. {e}")
                    prompt.ask_user_and_save()
                else:
                    raise

        return ecmwfapi.ECMWFService("mars", **kwargs)


source = MarsRetriever
