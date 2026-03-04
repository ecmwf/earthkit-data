# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import numpy as np
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.core.data import SimpleData
from earthkit.data.featurelist.simple import SimpleFeatureListBase
from earthkit.data.readers import Reader
from earthkit.data.utils.bbox import BoundingBox


class ShapeFileList(SimpleFeatureListBase):
    def __init__(self, path):
        self._path = path
        print(f"ShapeFileList: {path}")

    @thread_safe_cached_property
    def _features(self):
        return self._get_rows()

    def _get_rows(self, **kwargs):
        return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def ls(self, **kwargs):
        return self.to_pandas(**kwargs)

    def head(self, n=5, **kwargs):
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        return self.ls(n=-n, **kwargs)

    def to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self._path], **kwargs)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("Geojson handling requires 'geopandas' to be installed")

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def describe(self, *args, **kwargs):
        pass


class ShapeFileReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self.__gdf = None
        assert path.endswith(".shp")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def _repr_html_(self):
        html_repr = (
            f"<h4>{self.__class__.__name__}(represented as a geopandas object):</h3>"
            f"{self.to_pandas()._repr_html_()}"
        )

        return html_repr

    @property
    def _gdf(self):
        if self.__gdf is None:
            self.__gdf = self.to_pandas()
        return self.__gdf

    def __len__(self):
        return len(self._gdf)

    def __getitem__(self, n):
        return self._gdf.iloc[n]

    def mutate_source(self):
        # A ShapeFileReader is a source itself
        return self

    def bounding_box(self):
        return BoundingBox.from_geopandas(self._gdf)

    def ls(self, **kwargs):
        return self._gdf

    def head(self, **kwargs):
        return self._gdf.head(**kwargs)

    def tail(self, **kwargs):
        return self._gdf.tail(**kwargs)

    def describe(self, **kwargs):
        return self._gdf

    def to_numpy(self, flatten=False, **kwargs):
        v = self.to_pandas().to_numpy(**kwargs)
        if flatten:
            import math

            v = v.reshape(
                math.prod(v.shape),
            )
        return v

    def to_pandas(self, **kwargs):
        if not kwargs and self.__gdf is not None:
            return self.__gdf
        else:
            try:
                import geopandas as gpd
            except ImportError:
                raise ImportError("shapefile handling requires 'geopandas' to be installed")

            import numpy as np

            geo_df = gpd.read_file(self.path, **kwargs)
            return geo_df.set_index(np.arange(len(geo_df)))

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()


class ShapeFileData(SimpleData):
    _TYPE_NAME = "Shapefile"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return ["geopandas", "pandas", "xarray", "geojson"]

    def describe(self):
        return f"GeoJSON data from {self._reader.path}"

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_geopandas(self, **kwargs):
        return self._reader.to_geopandas(**kwargs)

    def to_featurelist(self, *args, **kwargs):
        return ShapeFileList(self._reader.path)

    def to_numpy(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        self._conversion_not_implemented()


SHAPE_EXT = ".shp"
MANDATORY = (".shp", ".shx", ".dbf")
NON_MANDATORY = (".sbn", ".sbx", ".shp.xml", ".prj", ".CPG")
DOUBLE_DOT_EXT = tuple([e for e in NON_MANDATORY if e.count(".") == 2])


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    root, extension = os.path.splitext(path)
    for e in DOUBLE_DOT_EXT:
        if path.endswith(e):
            root = path[: -len(e)]
            extension = e

    path = root + ".shp"

    # a shapefile consists of multiple files, but we only create
    # a reader for the .shp file
    if extension == SHAPE_EXT:
        if all(os.path.exists(root + e) for e in MANDATORY):
            return ShapeFileReader(source, path)
    else:
        if extension in MANDATORY or extension in NON_MANDATORY:
            from .unknown import UnknownReader

            return UnknownReader(source, "", skip_warning=True)
