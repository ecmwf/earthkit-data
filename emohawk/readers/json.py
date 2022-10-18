# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import json
import os

import geopandas as gpd

from . import Reader


class JSONReader(Reader):
    """
    Class for reading and polymorphing GeoJSON files.
    """

    def to_pandas(self, **kwargs):
        """
        Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return gpd.read_file(self.source, **kwargs)

    def to_json(self, file_name, **kwargs):
        """
        Save the data to a (Geo)JSON file.

        Parameters
        ----------
        file_name : str
            The file name to which the (Geo)JSON file will be saved.
        """
        self.save(file_name, **kwargs)

    def to_dict(self):
        """
        Return a dictionary respresentation of the JSON contents.

        Returns
        -------
        dict
        """
        with open(self.source, "r") as f:
            return json.load(f)

    def to_shapefile(self, file_name):
        """
        Save the data as an ESRI Shapefile.

        Parameters
        ----------
        file_name : str
            The file name to which the Shapefile will be saved.
        """
        original_file_name = None
        if file_name.endswith(".zip") and not file_name.endswith(".shp.zip"):
            original_file_name = file_name
            file_name = file_name.replace(".zip", ".shp.zip")
        self.to_pandas().to_file(file_name, driver="ESRI Shapefile")
        if original_file_name is not None:
            os.rename(file_name, original_file_name)


def reader(path, magic=None, deeper_check=False):
    try:
        with open(path, "r") as f:
            json.load(f)
    except:  # noqa: E722
        pass
    else:
        return JSONReader(path)
