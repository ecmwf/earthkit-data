# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging
import sys
from abc import ABCMeta
from abc import abstractmethod

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


if sys.version_info >= (3, 12):
    from itertools import batched
else:

    def batched(iterable, n):
        # batched('ABCDEFG', 3) --> ABC DEF G
        if n < 1:
            raise ValueError("n must be at least one")
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, n)):
            yield batch


class RequestBuilder:
    def __init__(self, owner, *args, request=None, normaliser=None, **kwargs):
        """Build requests from args, request and kwargs.

        Parameters
        ----------
        owner : Any
            The owner of the request builder.
        *args : tuple
            Positional arguments representing request dictionaries. Each item can be dictionary or a list/tuple of dictionaries.
        **kwargs : dict
            Keyword arguments representing request parameters.
        request : dict or list/tuple of dict, optional
            A single request dictionary or a list/tuple of request dictionaries.
        normaliser : callable, optional
            A function to normalise each request dictionary.

        Attributes
        ----------
        raw_requests : list of dict
            The raw request dictionaries before normalisation and splitting.
        requests : list of dict
            The final list of request dictionaries after normalisation and splitting.

        The following logic is applied to build the requests:

        1. Combine all dictionaries found in ``*args`` and ``request`` into a single list of
           request dictionaries.
        2. If ``**kwargs`` are provided, they are merged into each request dictionary. If only kwargs
           are provided (no ``request`` or ``*args`` specified), they form a single request dictionary.
        3. Each request dictionary is normalised using the `normaliser` function if provided.
        4. If a request dictionary contains the `split_on` key, the request is split into multiple
        requests based on the specified keys and their values.

        """
        self.owner = owner
        self.normaliser = normaliser or (lambda **r: r)
        assert callable(self.normaliser), self.normaliser
        self._raw = self._build_request_args(*args, request=request, **kwargs)
        self._requests = self._build()
        assert isinstance(self.requests, list), f"type={type(self.requests)}"

    def _build_request_args(self, *args, request=None, **kwargs):
        r = []
        if request is not None:
            r.extend(request if isinstance(request, (list, tuple)) else [request])

        for a in args:
            if not isinstance(a, (list, tuple)):
                a = [a]
            for aa in a:
                if not isinstance(aa, dict):
                    raise TypeError(f"{self.owner}: request arguments must be dictionaries! type={type(aa)}")
                r.append(aa)
        if kwargs:
            if not r:
                r.append(kwargs)
            else:
                r = [x.update(kwargs) or x for x in r]
        return r

    def _build(self):
        requests = []
        for request_item in self._raw:
            assert isinstance(request_item, dict), f"type={type(request_item)}"
            request = self.normaliser(**request_item)
            split_on = request.pop("split_on", None)
            if split_on is None:
                requests.append(request)
                continue

            if not isinstance(split_on, dict):
                split_on = {k: 1 for k in ensure_iterable(split_on)}
            for values in itertools.product(
                *[batched(ensure_iterable(request[k]), v) for k, v in split_on.items()]
            ):
                subrequest = dict(zip(split_on, values))
                requests.append({**request, **subrequest})
        return requests

    @property
    def raw_requests(self):
        return self._raw

    @property
    def requests(self):
        return self._requests


class FileRequestRetriever:
    def __init__(self, owner, retriever=None):
        self.owner = owner
        self.retriever = retriever
        assert callable(self.retriever), self.retriever

    def retrieve(self, requests, *extra_args):
        nthreads = min(self.owner.config("number-of-download-threads"), len(requests))

        if nthreads < 2:
            path = [self.retriever(r, *extra_args) for r in requests]
        else:
            from earthkit.data.utils.progbar import tqdm

            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self.retriever, r, *extra_args) for r in requests]

                iterator = (f.result() for f in futures)
                path = list(tqdm(iterator, leave=True, total=len(requests)))

        return path


class RequestMapper(metaclass=ABCMeta):
    metadata_alias = None

    def __init__(self, request, **kwargs):
        self.request = request

    @thread_safe_cached_property
    def field_requests(self):
        return self._build()

    @abstractmethod
    def _build(self):
        pass

    def request_at(self, index):
        return self.field_requests[index]

    def __len__(self):
        return len(self.field_requests)
