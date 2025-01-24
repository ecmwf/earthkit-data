# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

try:
    from hda.api import DataOrderRequest  # noqa
except ImportError:
    raise ImportError("WEkEO access requires 'hda' to be installed")

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import normalize

from .file import FileSource
from .wekeo import EXTENSIONS
from .wekeo import ApiClient as WekeoClient
from .wekeo import HDAAPIKeyPrompt

LOG = logging.getLogger(__name__)


class ApiClient(WekeoClient):
    name = "wekeocds"

    def __int__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def retrieve(self, name, request, target=None):
        rq = {"dataset_id": name}
        rq.update(
            {
                _name: (
                    _value
                    if isinstance(_value, list) or _name in ("data_format", "download_format")
                    else [_value]
                )
                for _name, _value in request.items()
            }
        )

        if "area" in request:
            rq.update({"bbox": request["area"]})

        request["request"] = rq

        return super().retrieve(name, request, target)


class WekeoCdsRetriever(FileSource):
    sphinxdoc = """
    WekeoCdsRetriever
    """

    def __init__(self, dataset, *args, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt

        assert isinstance(dataset, str)
        if len(args):
            assert len(args) == 1
            assert isinstance(args[0], dict)
            assert not kwargs
            kwargs = args[0]

        requests = self.requests(**kwargs)

        self.client(self.prompt)  # Trigger password prompt before threading

        nthreads = min(self.config("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(dataset, r) for r in requests]
        else:
            from earthkit.data.utils.progbar import tqdm

            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self._retrieve, dataset, r) for r in requests]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

    def _retrieve(self, dataset, request):
        def retrieve(target, args):
            self.client(self.prompt).retrieve(args[0], args[1], target)

        return self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )

    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def requests(self, **kwargs):
        split_on = kwargs.pop("split_on", None)
        if split_on is None or not isinstance(kwargs.get(split_on), (list, tuple)):
            return [kwargs]

        result = []

        for v in kwargs[split_on]:
            r = dict(**kwargs)
            r[split_on] = v
            result.append(r)

        return result

    @staticmethod
    def client(use_prompt):
        if use_prompt:
            prompt = HDAAPIKeyPrompt()
            prompt.check()

            try:
                return ApiClient()
            except Exception as e:
                # if no rc file is available hda throws
                # ConfigurationError: Missing or incomplete configuration
                if ".hdarc" in str(e) or not prompt.has_config_env():
                    LOG.warning(e)
                    LOG.exception(f"Could not load hda client. {e}")
                    prompt.ask_user_and_save()
                    return ApiClient()
                raise
        else:
            return ApiClient()


source = WekeoCdsRetriever
