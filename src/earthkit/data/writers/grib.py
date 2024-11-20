# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import Writer


class GribWriter(Writer):
    DATA_FORMAT = "grib"

    def write(self, f, field, values=None, check_nans=True, bits_per_value=None):
        r"""Write a GRIB field to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        values: ndarray
            Values of the GRIB field.
        metadata: :class:`GribMetadata`
            Metadata of the GRIB field.
        check_nans: bool
            Replace nans in ``values`` with GRIB missing values when writing to ``f``.
        bits_per_value: int or None
            Set the ``bitsPerValue`` GRIB key in the generated GRIB message. When
            None the ``bitsPerValue`` stored in the metadata will be used.
        """

        from earthkit.data.readers.grib.output import new_grib_output

        output = new_grib_output(f, template=field)

        md = {}
        # wrapped metadata
        if hasattr(field._metadata, "extra"):
            md = {k: field._metadata._extra_value(k) for k, v in field._metadata.extra.items()}

        if bits_per_value is not None:
            if field._metadata.get("bitsPerValue", 0) != bits_per_value:
                md["bitsPerValue"] = bits_per_value

        # keep the original generatingProcessIdentifier if not set
        if "generatingProcessIdentifier" not in md:
            md["generatingProcessIdentifier"] = None

        if values is None:
            try:
                if field._has_new_values():
                    values = field.values
            except AttributeError:
                pass

        output.write(values, check_nans=check_nans, missing_value=field.handle.MISSING_VALUE - 1, **md)


Writer = GribWriter
