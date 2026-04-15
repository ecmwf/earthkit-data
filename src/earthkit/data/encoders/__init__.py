# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
from abc import ABCMeta, abstractmethod
from importlib import import_module

LOG = logging.getLogger(__name__)


"""Assign encoders to file suffixes"""
_SUFFIXES = {
    (".grib", ".grb", ".grib1", ".grib2", ".grb1", ".grb2"): "grib",
    (".nc", ".nc3", ".nc4", ".netcdf"): "netcdf",
    (".tiff", ".tif"): "geotiff",
    (".bufr",): "bufr",
    (".odb",): "odb",
}


def _suffix_to_encoder(suffix):
    for suffixes, encoder in _SUFFIXES.items():
        if isinstance(suffixes, str):
            if suffix == suffixes:
                return encoder
        elif suffix in suffixes:
            return encoder


class EncodedData(metaclass=ABCMeta):
    """Base class for representing encoded data.

    It is meant to be used by a :class:`Target` to write/add data to a given target.
    It is the return value from the :meth:`Encoder.encode` method.
    """

    prefer_file_path = False

    @abstractmethod
    def to_bytes(self):
        """Return the data as a bytesarray."""
        pass

    @abstractmethod
    def to_file(self, f):
        """Write the data to a file.

        Parameters
        ----------
        f: file-like object
            File-like object to write to
        """
        pass

    @abstractmethod
    def get(self, key, default=None):
        pass


class FilePathEncodedData(EncodedData):
    def __init__(self, path, binary):
        self.path = path
        self.binary = binary

    def to_bytes(self):
        raise NotImplementedError

    def to_file(self, f, **kwargs):
        mode = "rb" if self.binary else "r"
        with open(self.path, mode) as g:
            while True:
                chunk = g.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    def get(self, key, default=None):
        raise NotImplementedError


class Encoder(metaclass=ABCMeta):
    """Base class for encoders.

    An encoder is used to encode data to a specific format that can be used by a :class:`Target`.

    Parameters
    ----------
    template: obj, None
        The template to use to encode the data. Can be overridden in the :obj:`encode` method.
    metadata: dict, None
        Metadata to use when encoding the data. Can be overridden in the :obj:`encode` method.
    **kwargs:
        Additional keyword arguments
    """

    def __init__(self, template=None, metadata=None, **kwargs):
        self.template = template
        self.metadata = metadata or {}
        self.metadata.update(kwargs)

    @abstractmethod
    def encode(
        self,
        data=None,
        values=None,
        check_nans=False,
        metadata={},
        template=None,
        missing_value=9999,
        target=None,
        **kwargs,
    ) -> EncodedData:
        """Encode the data.

        Parameters
        ----------
        data: obj, None
            The data to encode. Should be used via double dispatch. Must have an ``_encode()``
            method,  which will call the appropriate ``_encode_*`` method on the :class:`Encoder`.
        values: obj, None
            The values to encode.
        check_nans: bool
            If True, check for NaN values in the data and replace them with the ``missing_value``.
        metadata: dict
            Metadata to use when encoding the data. When None,
            the metadata the :class:`Encoder` was created with will be used if available.
        template: obj, None
            The template to use to encode the data. When None,
            the template the :class:`Encoder` was created with will be used if available.
        missing_value: number
            The value to use for missing values.
        target: Target, None
            The target to write to. Can be used by the encoder to determine how to encode the data. When None, the encoder will determine the target from the data to write (if possible) or from the :class:`Encoder` properties.
        **kwargs: dict
            Additional keyword arguments.

        Returns
        -------
        EncodedData
            The encoded data.
        """
        pass

    @abstractmethod
    def _encode(self, data, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic.

        Parameters
        ----------
        field: :obj:`Base`
            The data to encode

        Double dispatch method that called from a ``data`` to encode itself.
        """
        pass

    @abstractmethod
    def _encode_field(self, field, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic for a Field.

        Parameters
        ----------
        field: :obj:`Field`
            The Field to encode

        Double dispatch method that called from ``field`` to encode itself.
        """
        pass

    @abstractmethod
    def _encode_fieldlist(self, fieldlist, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic for a FieldList.

        Parameters
        ----------
        fieldlist: :obj:`FieldList`
            The FieldList to encode

        Double dispatch method that called from ``fieldlist`` to encode itself.
        """
        pass

    @abstractmethod
    def _encode_xarray(self, data, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic for Xarray data.

        Parameters
        ----------
        data: Xarray DataArray or Dataset
            The data to encode

        Double dispatch method that called from ``data`` to encode itself.
        """
        pass

    @abstractmethod
    def _encode_featurelist(self, featurelist, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic for a FeatureList.

        Parameters
        ----------
        featurelist: :obj:`FeatureList`
            The FeatureList to encode

        Double dispatch method that called from ``featurelist`` to encode itself.
        """
        pass

    @abstractmethod
    def _encode_path(self, path_info, *, target=None, **kwargs) -> EncodedData:
        """Subclass implementation of the encoding logic for a path.

        Parameters
        ----------
        path_info: :obj:`PathInfo`
            The PathInfo to encode

        Double dispatch method that called from ``featurelist`` to encode itself.
        """
        pass


class EncoderLoader:
    kind = "encoder"

    def load_module(self, module):
        return import_module(module, package=__name__).encoder

    def load_entry(self, entry):
        entry = entry.load()
        if callable(entry):
            return entry
        return entry.encoder

    def load_remote(self, name):
        return None


class EncoderMaker:
    ENCODERS = {}

    def __call__(self, name_or_encoder, *args, **kwargs):
        if isinstance(name_or_encoder, Encoder):
            return name_or_encoder

        name = name_or_encoder

        loader = EncoderLoader()

        if name in self.ENCODERS:
            klass = self.ENCODERS[name]
        else:
            from earthkit.data.core.plugins import find_plugin

            klass = find_plugin(os.path.dirname(__file__), name, loader)
            self.ENCODERS[name] = klass

        encoder = klass(*args, **kwargs)

        if getattr(encoder, "name", None) is None:
            encoder.name = name

        return encoder

    def __getattr__(self, name):
        return self(name.replace("_", "-"))


create_encoder = EncoderMaker()


def make_encoder(data, encoder=None, suffix=None, metadata=None, **kwargs):
    if isinstance(encoder, Encoder):
        encoder.metadata.update(metadata or {})
        return encoder

    # print("make_encoder", data, encoder, suffix, metadata, kwargs)

    if encoder is None:
        if suffix is not None:
            encoder = _suffix_to_encoder(suffix)
        if encoder is None:
            from earthkit.data.data import Data

            # print("make_encoder1", data, suffix)
            if hasattr(data, "_default_encoder"):
                encoder = data._default_encoder()
            # print("make_encoder2", encoder, data)
            if (
                encoder is None
                and isinstance(data, Data)
                and hasattr(data, "_source")
                and hasattr(data._source, "_default_encoder")
            ):
                encoder = data._source._default_encoder()

    if isinstance(encoder, str):
        encoder = create_encoder(encoder, metadata=metadata, **kwargs)
        assert encoder is not None
        return encoder

    if encoder is not None:
        raise ValueError(f"Unsupported encoder={encoder}. Must be a str or Encoder")

    assert encoder is None

    raise ValueError("Cannot determine encoder type")
