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


class S3Retriever(FileSource):
    def __init__(self, request) -> None:
        super().__init__()

        if not isinstance(request, list):
            request = [request]

        p = [self._proc_request(r) for r in request]
        self.path = []
        for r in p:
            self.path.extend(r)

        print(f"self.path={self.path}")

    def __repr__(self) -> str:
        return self.__class__.__name__

    def _proc_request(self, request):
        result = []
        bucket = request["bucket"]
        for obj in request["objects"]:
            path = bucket + "/" + obj["object"]
            result.append(self._retrieve(path))
        return result

    def _retrieve(self, path):
        def retrieve(target, path):
            import s3fs

            s3 = s3fs.S3FileSystem(anon=True)
            with s3.open(path, "rb") as f:
                s3.get_file(f, target)

        return self.cache_file(
            retrieve,
            path,
        )


source = S3Retriever
