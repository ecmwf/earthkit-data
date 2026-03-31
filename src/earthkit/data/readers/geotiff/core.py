# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .. import Reader

DEFAULT_XARRAY_KWARGS = {
    # Splitting bands into individual variables preserves band-specific metadata.
    "band_as_variable": True,
    # Mask and scale values by default to match xarray's default behaviour.
    # Note: masked values are set to NaN, so all values are returned as floats.
    "mask_and_scale": True,
    "decode_times": True,
}


class GeoTIFFReaderBase(Reader):
    _format = "geotiff"
    _binary = True
    _appendable = True
