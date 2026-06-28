# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.sources import Source

from .core import ShapefileReaderBase


class ShapeFileReader(Source, ShapefileReaderBase):
    def __init__(self, source, path):
        assert path.endswith(".shp")
        self._ori_source = source
        ShapefileReaderBase.__init__(self, source, path)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    def to_featurelist(self, *args, **kwargs):
        from .file import ShapeFileList

        return ShapeFileList(self.path)

    def to_numpy(self, flatten=False, **kwargs):
        v = self.to_pandas().to_numpy(**kwargs)
        if flatten:
            import math

            v = v.reshape(
                math.prod(v.shape),
            )
        return v

    def to_pandas(self, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("shapefile handling requires 'geopandas' to be installed")

        import numpy as np

        geo_df = gpd.read_file(self.path, **kwargs)
        return geo_df.set_index(np.arange(len(geo_df)))

    def mutate_source(self):
        # A ShapeFileReader is a source itself
        return self

    def to_data_object(self):
        from earthkit.data.data.shapefile import ShapeFileData

        return ShapeFileData(self)

    def _encode_default(self, encoder, **kwargs):
        return None
