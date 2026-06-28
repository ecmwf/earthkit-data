# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .. import Reader


class PPReaderBase(Reader):
    _format = "pp"
    _binary = True
    _appendable = False

    def _open_pp(
        self,
        *,
        iris_open_kwargs: dict | None = None,
        iris_save_kwargs: dict | None = None,
        xr_load_kwargs: dict | None = None,
    ):
        try:
            import iris
        except ImportError:
            raise ImportError("PP file handling requires 'iris' to be installed")

        try:
            from ncdata.iris_xarray import cubes_to_xarray
        except ImportError:
            raise ImportError("PP file handling requires 'ncdata' to be installed")

        cubelist = iris.load(self.path, **iris_open_kwargs or {})
        return cubes_to_xarray(cubelist, iris_save_kwargs=iris_save_kwargs, xr_load_kwargs=xr_load_kwargs)
