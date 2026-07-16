# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Encoding/decoding utilities for the ``_earthkit`` xarray attribute and the
``EarthkitAttrsBuilder`` that constructs it from GRIB field metadata.
"""

import base64
import json

ACCESSOR_KEY = "_earthkit"


# ---------------------------------------------------------------------------
# JSON encoding/decoding for the _earthkit attribute
# ---------------------------------------------------------------------------

_BYTES_MARKER = "__bytes_b64__"


class _EarthkitEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles bytes (via base64) and nested dicts."""

    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return {_BYTES_MARKER: base64.b64encode(obj).decode("ascii")}
        return super().default(obj)


def _earthkit_object_hook(obj):
    """JSON object_hook that restores base64-encoded bytes."""
    if _BYTES_MARKER in obj and len(obj) == 1:
        return base64.b64decode(obj[_BYTES_MARKER])
    return obj


def encode_earthkit_attrs(d):
    """Encode a dict into a JSON string suitable for storage in xarray attrs.

    Handles bytes values (via base64), nested dicts, and other JSON-serializable types.

    Parameters
    ----------
    d : dict
        The dictionary to encode.

    Returns
    -------
    str
        A JSON string representation of the dictionary.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Expected dict, got {type(d)}")
    return json.dumps(d, cls=_EarthkitEncoder)


def decode_earthkit_attrs(s):
    """Decode an _earthkit attribute value back to a dict.
    Restores base64-encoded bytes to their original form.

    Parameters
    ----------
    s : str
        The attribute value to decode.

    Returns
    -------
    dict or None
        The decoded dictionary, or None if decoding fails.
    """
    if s is None:
        return None
    if isinstance(s, str):
        try:
            return json.loads(s, object_hook=_earthkit_object_hook)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


# ---------------------------------------------------------------------------
# EarthkitAttrsBuilder
# ---------------------------------------------------------------------------


class EarthkitAttrsBuilder:
    @staticmethod
    def _grid_spec_dict(field):
        """Return grid_spec as a dict (not a JSON string)."""
        try:
            return field.geography.grid_spec()
        except Exception:
            return None

    def build(self, field):
        """Build the _earthkit attribute dict for a field and encode it to JSON.

        Returns a dict ``{ACCESSOR_KEY: <json_string>}`` suitable for merging into
        ``da.attrs``.
        """
        res = dict()
        grid_spec = self._grid_spec_dict(field)

        bpv = None
        try:
            md = field._get_grib().message(deflate=True)
            bpv = field._get_grib().get_extra_key("bitsPerValue", default=None)
            if bpv is None:
                bpv = field.get("metadata.bitsPerValue", default=None)
        except Exception:
            md = b""

        attrs = {
            "message": md,
        }

        if bpv is not None and bpv != 0:
            attrs["bitsPerValue"] = bpv

        if grid_spec is not None:
            attrs["grid_spec"] = grid_spec

        res[ACCESSOR_KEY] = encode_earthkit_attrs(attrs)

        return res

    def set_field(self, field, da_attrs):
        """Update the _earthkit attribute with a new field's metadata."""
        res = dict()

        grid_spec = self._grid_spec_dict(field)

        attrs_ori = decode_earthkit_attrs(da_attrs.get(ACCESSOR_KEY)) or {}
        attrs = attrs_ori.copy()

        try:
            message = field._get_grib().message(deflate=True)
        except Exception:
            message = b""

        if message:
            attrs["message"] = message
        elif "message" in attrs:
            del attrs["message"]

        if grid_spec is not None:
            attrs["grid_spec"] = grid_spec
        elif "grid_spec" in attrs:
            del attrs["grid_spec"]

        res[ACCESSOR_KEY] = encode_earthkit_attrs(attrs)
        return res

    def set_grid_spec(self, grid_spec, da_attrs):
        """Update only the grid_spec in the _earthkit attribute."""
        res = dict()

        if not isinstance(grid_spec, dict):
            raise ValueError(f"Invalid grid_spec: {grid_spec}. Must be a dict.")

        attrs_ori = decode_earthkit_attrs(da_attrs.get(ACCESSOR_KEY)) or {}
        attrs = attrs_ori.copy()
        attrs["grid_spec"] = grid_spec

        res[ACCESSOR_KEY] = encode_earthkit_attrs(attrs)

        return res
