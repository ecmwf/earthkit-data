# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import geopandas as gpd

from . import Reader


class ShapefileReader(Reader):
    """
    Class for reading and polymorphing ESRI Shapefiles.
    """

    def to_pandas(self, **kwargs):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return gpd.read_file(self.source, **kwargs)

    def to_json(self, file_name):
        """
        Save the data to a GeoJSON file.

        Parameters
        ----------
        See `pandas.DataFrame.to_file`.
        """
        self.to_pandas().to_file(file_name, driver="GeoJSON")
