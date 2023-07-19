# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# The code is copied from skinnywms, and we should combile later

import mimetypes
import numpy as np

from . import Reader


class GeojsonReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self.fields = None

    def _scan(self):
        """
        For geojson, a field is a feature
        """
        if self.fields is None:
            self.fields = self.get_fields()

    def __repr__(self):
        return "GeojsonReader(%s)" % (self.path,)

    def __iter__(self):
        """
        Iterate over features in geojson via pandas
        """
        self._scan()
        return iter(self.fields)
    
    def __len__(self):
        self._scan()
        return len(self.fields)

    def __getitem__(self, n):
        self._scan()
        return self.fields[n]
    
    def bounding_box(self, **kwargs):
        return self.to_pandas(**kwargs).crs.area_of_use.bounds
    
    def ls(self, **kwargs):
        return self.to_pandas(**kwargs)
    describe = ls
    # def describe(self, kwargs):
    #     return self.to_pandas(**kwargs)

    def get_fields(self, **kwargs):
        return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def to_numpy(self, flatten=False):
        arr = self.to_pandas().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    # def to_geopandas(self, **kwargs):
    #     # TODO: handle multiple paths
    #     return self.to_pandas(**kwargs)
    
    def to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self.path], **kwargs)
    to_geopandas = to_pandas

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        import geopandas as gpd

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def bounding_box(self):
        return [s.bounding_box() for s in self.get_fields()]


def reader(source, path, magic=None, deeper_check=False):
    kind, compression = mimetypes.guess_type(path)
    ext = path.split('.')[-1]

    geojson_extensions = ['geojson']
    geojson_mimetypes = ('application/geo+json')
    if magic is None or ext in geojson_extensions or kind in geojson_mimetypes:
        return GeojsonReader(source, path)
