# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)


# class TemplateHandleMaker:
#     """Create a new GribCodesHandle from a template."""

#     def __init__(self, template=None):
#         self.template = self.handle_from_template(template, clone=False)
#         self._bbox = {}

#     def make(self, values_shape=None, template=None, field_metadata=None):
#         """Create a new GribCodesHandle from a template, field or metadata.

#         May modify existing metadata

#         Parameters
#         ----------
#         values_shape: tuple, optional
#             The shape of the values to encode
#         metadata: dict, optional
#             Metadata to encode
#         template: GribCoder, optional
#             A template to use for encoding
#         field_metadata: dict, optional
#             Metadata to be set on the field before encoding.
#         """
#         if template is None:
#             template = self.template

#         handle = self.handle_from_template(
#             template, values_shape=values_shape, field_metadata=field_metadata, clone=True
#         )


#         # if handle is None:
#         #     if values_shape is None:
#         #         raise ValueError("No values to encode")
#         #     if field_metadata:
#         #         raise ValueError("Cannot provide field_metadata without a template or handle")
#         #     handle = self.handle_from_metadata(values_shape, metadata, _COMPULSORY)

#         return handle


def handle_from_template(template, values_shape=None, field_metadata=None, clone=True):
    """Create a new GribCodesHandle from a template, field or metadata.

    May modify existing metadata

    Parameters
    ----------
    values_shape: tuple, optional
        The shape of the values to encode
    metadata: dict, optional
        Metadata to encode
    template: GribCoder, optional
        A template to use for encoding
    field_metadata: dict, optional
        Metadata to be set on the field before encoding.
    """
    handle = None
    if template is not None:
        from earthkit.data.core.field import Field

        def _result(handle):
            if field_metadata:
                from earthkit.data.field.grib.create import create_grib_field

                field = create_grib_field(handle)
                field = field.set(**field_metadata)
                # it clones the handle internally, so we don't need to clone it again here
                return handle_from_field(field)
            return handle.clone() if clone else handle

        if isinstance(template, Field):
            if field_metadata:
                template = template.set(**field_metadata)
            return handle_from_field(template, values_shape=values_shape)
        # GribMetadata or GribHandle
        elif hasattr(template, "handle"):
            handle = template.handle
            if handle is not None:
                return _result(handle)
        else:
            from earthkit.data.readers.grib.handle import GribCodesHandle

            if isinstance(template, GribCodesHandle):
                return _result(template)

            # message buffer as bytes
            elif isinstance(template, bytes):
                handle = GribCodesHandle.from_message(template)
                if handle is not None:
                    return _result(handle)
            # GRIB sample as string
            elif isinstance(template, str):
                handle = GribCodesHandle.from_sample(template)
                if handle is not None:
                    return _result(handle)
            # raw ecCodes handle
            elif isinstance(template, int):
                try:
                    handle = GribCodesHandle._from_raw_handle(template)
                    if handle is not None:
                        return _result(handle)
                except Exception:
                    pass

    return None


def handle_from_field(field, values_shape=None):
    r = {}
    field = field.sync()
    field._get_grib_context(r)
    handle = r.pop("handle", None)

    if handle is not None:
        handle = handle.clone()
        if values_shape is None:
            if "values" in r:
                handle.set_values(r["values"])

    return handle
