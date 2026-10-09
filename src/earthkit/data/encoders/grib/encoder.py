# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging

from earthkit.data.decorators import normalise, normalise_grib_keys
from earthkit.data.utils.dates import step_range_to_grib

from .. import EncodedData, Encoder, FilePathEncodedData
from .mars import handle_from_mars
from .metadata import handle_from_metadata
from .template import handle_from_template

LOG = logging.getLogger(__name__)

_NOT_IN_EDITION_1 = (
    "productDefinitionTemplateNumber",
    "typeOfGeneratingProcess",
)

_COMPULSORY = (("date", "referenceDate"), ("param", "paramId", "shortName"))


class GribEncodedData(EncodedData):
    """The object representing the encoded GRIB message."""

    def __init__(self, handle, template_field=None):
        """Initialize the GribEncodedData object.

        Parameters
        ----------
        handle: GribCodesHandle
            The handle to the GRIB message.
        template_field: Field, optional
            A template field to use when converting to a Field object. This is
            used to provide extra field data (e.g. labels) that cannot be obtained
            from the GRIB message itself.
        """
        self.handle = handle
        self._template_field = template_field

    def to_bytes(self):
        """Return the GRIB message as bytes."""
        return self.handle.get_buffer()

    def to_file(self, f):
        """Write the GRIB message to a file.

        Parameters
        ----------
        f: file-like object
            The file-like object to write the GRIB message to.

        """
        self.handle.write(f)

    def get(self, key, default=None):
        """Get a value from the GRIB message metadata.

        Parameters
        ----------
        key: str
            The key of the metadata to retrieve.
        default: any, optional
            The default value to return if the key is not found.

        Returns
        -------
        The value associated with the key, or the default value if the key is not found.
        """
        if key.startswith("metadata."):
            return self.handle.get(key[9:], default=default)
        elif key:
            return self.to_field().get(key, default=default)
        else:
            raise NotImplementedError

    def to_field(self):
        """Convert the GRIB message to a Field object."""
        from earthkit.data.field.grib.create import create_grib_field_from_message

        return create_grib_field_from_message(self.to_bytes(), template_field=self._template_field)


class Combined:
    def __init__(self, handle, metadata):
        self.handle = handle
        self.metadata = metadata

    def __contains__(self, key):
        # return key in self.metadata or key in self.handle
        raise NotImplementedError()

    def __getitem__(self, key):
        if key in self.metadata:
            return self.metadata[key]
        return self.handle.get(key, default=None)


class GribEncoder(Encoder):
    """Encoder for GRIB format.

    This class is used to encode data to GRIB format via the :meth:`encode` method.

    Parameters
    ----------
    template: Field, GribCodesHandle, bytes, str, int, None
        A preset template to use for encoding when :meth:`encode` is called without a template.
        It can be a :py:class:`~earthkit.data.core.field.Field`,
        a :py:class:`~earthkit.data.reader.grib.GribCodesHandle`, a GRIB message as
        bytes, an ecCodes GRIB sample name as string, a raw ecCodes handle as an integer, or None.
        See :meth:`encode` for more details on how the template is used.
    metadata: dict
        A preset metadata to encode. The keys must be ecCodes GRIB keys, optionally prefixed with "metadata.".
        This metadata is used as default when :meth:`encode` is called without metadata. If metadata is provided
        in the :meth:`encode` method, it is merged with this preset metadata, with the metadata provided
        in the :meth:`encode` method taking precedence.
    mars_metadata: dict, optional
        A preset of MARS metadata keys/values used as default when :meth:`encode` is called without
        ``mars_metadata``. If ``mars_metadata`` is provided in the :meth:`encode` method, it is merged with
        this preset, with the ``mars_metadata`` provided in the :meth:`encode` method taking precedence.
        Cannot be specified together with ``template``.
    kwargs: dict
        Additional keyword arguments interpreted as metadata to encode. The keys must be ecCodes GRIB keys,
        optionally prefixed with "metadata.".

    Examples
    --------
    See the howto examples for more details and examples of encoding GRIB data with :class:`GribEncoder`.

    - :ref:`/tutorials/target/grib_encoder.ipynb`
    - :ref:`/tutorials/target/grib_encoder_mars.ipynb`
    - :ref:`/tutorials/grib/grib_modify_metadata.ipynb`
    - :ref:`/tutorials/grib/grib_modify_values.ipynb`

    Using with a preset template and metadata:

    >>> import earthkit.data as ekd
    >>> template = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    >>> template.get("metadata.shortName")
    '2t'
    >>> encoder = GribEncoder(template=template, metadata={"shortName": "msl"})
    >>> d = encoder.encode(values=template.values + 1.0, step=6)
    >>> f = d.to_field()
    >>> f.get("parameter.variable")
    'msl'
    >>> f.get("parameter.shortName")
    'msl'
    >>> f.get("parameter.units")
    'hPa'
    >>> f.get("step")
    6

    Using without preset template and metadata:
    >>> encoder = GribEncoder()
    >>> d = encoder.encode(values=template.values + 1.0, metadata={"shortName": "msl"}, step=6)
    >>> f = d.to_field()
    >>> f.get("parameter.variable")
    'msl'
    >>> f.get("parameter.shortName")
    'msl'
    >>> f.get("parameter.units")
    'hPa'
    >>> f.get("step")
    6
    """

    def __init__(self, template=None, metadata=None, mars_metadata=None, **kwargs):
        super().__init__(template=template, metadata=metadata, **kwargs)
        # the template is stored as a handle to be used as a basis for encoding,
        # (when available)
        self._template_field = None
        if template is not None:
            from earthkit.data import Field

            if isinstance(template, Field):
                self._template_field = template

        if mars_metadata and template:
            raise NotImplementedError("mars_metadata cannot be used together with a template")

        self.mars_metadata = mars_metadata
        self.template = handle_from_template(self.template, clone=False)

    @normalise_grib_keys
    @normalise("date", "date")
    def _normalise_kwargs_names(self, **kwargs):
        return kwargs

    def _normalise_metadata_key_names(self, metadata):
        def _convert(name):
            if name.startswith("metadata."):
                return name[9:]
            return name

        return {_convert(k): v for k, v in metadata.items()}

    def _separate_metadata(self, metadata):
        field = {}
        ecc = {}
        for k, v in metadata.items():
            if "." in k:
                field[k] = v
            else:
                ecc[k] = v

        return field, ecc

    def encode(
        self,
        data=None,
        values=None,
        check_nans=True,
        metadata=None,
        mars_metadata=None,
        template=None,
        missing_value=9999,
        target=None,
        **kwargs,
    ):
        """
        Encode new GRIB message(s).

        Parameters
        ----------
        data: Field, FieldList, Numpy array, or None
            The data to encode. Can be a :py:class:`~earthkit.data.core.field.Field`, a
            :py:class:`~earthkit.data.core.fieldlist.FieldList`, a Numpy array, or None.
            If None, the new GRIB message(s) will be created from the ``values``, ``metadata`` and
            ``template``. Cannot be specified together with ``values`` and ``template``.
            When ``template`` is also provided, it will be used as a basis for encoding,
            but the values will be taken from ``data``.
        values: numpy.ndarray or None
            The values to encode. If None, the values will be taken from the ``data`` or
            ``template``. Takes precedence over the values in ``data`` or ``template``
            if any of them are provided. If the values contain NaNs, they will be replaced with the
            ``missing_value`` provided. Cannot be specified together with ``data`` and ``template``.
        check_nans: bool
            Check for NaNs in the values and replace them with ``missing_value``.
        metadata: dict
            Metadata to encode. The keys can be ecCodes GRIB keys, optionally prefixed with "metadata."
            The format independent keys from :py:class:`~earthkit.data.core.field.Field` metadata are also
            accepted. If format independent keys are provided, they are applied first to create a new handle,
            then if ecCodes GRIB keys are provided too, they are applied on top of the handle.
        mars_metadata: dict, optional
            MARS metadata keys/values (e.g. ``class``, ``stream``, ``type``, ``expver``, ``date``, ``time``,
            ``step``, ``param``, ``levtype``, ``grid``, etc.) used to build a new GRIB message directly from
            ``values``, without a ``template`` or ``data``. Internally, this uses the `metkit
            <https://github.com/ecmwf/metkit>`_ package to turn the MARS-style request into a GRIB message.
            ``values`` is mandatory when ``mars_metadata`` is used. Cannot be specified together with
            ``template`` or ``data``, since ``mars_metadata`` builds the message from scratch. Can be combined
            with ``metadata``, in which case the GRIB message is first created from ``mars_metadata`` and
            ``values``, then the keys in ``metadata`` are set on top of it. This is useful for GRIB keys that
            are not part of the MARS vocabulary, such as ``bitsPerValue``. If a preset ``mars_metadata`` was
            given to :obj:`GribEncoder`, it is merged with the ``mars_metadata`` provided here, with the
            latter taking precedence.
        template: Field, GribCodesHandle, bytes, str, int, None
            A template to use for encoding. It can be a :py:class:`~earthkit.data.core.field.Field`,
            a :py:class:`~earthkit.data.reader.grib.GribCodesHandle`, a GRIB message as
            bytes, an ecCodes GRIB sample name as string, a raw ecCodes handle as an integer, or None. If None, a
            the :obj:`GribEncoder.template` will be used if provided. Otherwise a new handle will be
            created from the ``data``, ``values`` and ``metadata``. Takes precedence over the
            ``data`` in forming the new GRIB message, but values are taken from the ``data`` if no
            provided directly. Cannot be specified together with ``data`` and ``values``.
        missing_value: float
            The value to use for NaNs. Default is 9999, which is the default missing value used by ecCodes
            when encoding with a template that does not have a valid "bitsPerValue" key.
        kwargs: dict
            Additional metadata to encode.

        Returns
        -------
        :obj:`GribEncodedData` or generator of :obj:`GribEncodedData`
            The object representing the encoded GRIB message(s). When a single GRIB message is encoded,
            a :obj:`GribEncodedData` object is returned. When multiple GRIB messages are encoded, a generator
            of :obj:`GribEncodedData` objects is returned that can be processed in a loop.

        Notes
        -----
        ``data``, ``values`` and ``template`` cannot be specified together. If more than one of them
        are provided, the following rules applied:

        - ``data``, ``value``:  The values will be taken from the ``values`` argument.
        - ``data``, ``template``: The ``template`` will be used as a basis for encoding, but
            the values will be taken from the ``data`` argument.
        - ``values``, ``template``: The ``template`` will be used as a basis for encoding, but
            the values will be taken from the ``values`` argument.

        When no ``data`` and ``template`` are provided, a new GRIB message will be created either from
        ``mars_metadata`` or from ``values`` and ``metadata``:

        - If ``mars_metadata`` is given, it is used together with ``values`` to build the message via
          `metkit <https://github.com/ecmwf/metkit>`_. Any ``metadata`` provided is then applied on
          top of the resulting message.
        - Otherwise, the message is created from ``values`` and ``metadata`` alone. This is an experimental
          feature and only works for certain metadata keys and the grid has to be either global lat-lon or
          reduced Gaussian grid. The geography is inferred from the shape of the specified ``values``.

        Examples
        --------
        See the howto examples for more details and examples of encoding GRIB data with :class:`GribEncoder`.

        - :ref:`/tutorials/target/grib_encoder.ipynb`
        - :ref:`/tutorials/target/grib_encoder_mars.ipynb`
        """
        template_field = None
        if template is None:
            template = self.template
            template_field = self._template_field
        else:
            from earthkit.data import Field

            if isinstance(template, Field):
                template_field = template

        if data is not None and values is not None and template:
            raise ValueError("Cannot provide data, values and template together")

        mars_metadata = {} if mars_metadata is None else mars_metadata
        mmd = {} if self.mars_metadata is None else self.mars_metadata.copy()
        mmd.update(**mars_metadata)
        mars_metadata = mmd

        if mars_metadata:
            if template is not None or data is not None:
                raise ValueError("Cannot provide mars_metadata when a template or data is specified")
            if values is None:
                raise ValueError("When providing mars_metadata, values must also be specified")

        metadata = metadata if metadata is not None else {}
        md = self._normalise_kwargs_names(**self.metadata)
        md.update(self._normalise_kwargs_names(**metadata))
        md.update(self._normalise_kwargs_names(**kwargs))
        md = self._normalise_metadata_key_names(md)

        # separate the metadata into format independent field metadata and
        # raw ecCodes GRIB metadata
        field_metadata, ecc_metadata = self._separate_metadata(md)

        # when the input date is a datetime object time can be inferred from it
        can_infer_time = (
            "date" in ecc_metadata
            and isinstance(md["date"], datetime.datetime)
            and not self._has_standard_date_input([self.metadata, metadata, kwargs])
        )

        kwargs = dict()
        kwargs["values"] = values
        kwargs["check_nans"] = check_nans
        kwargs["metadata"] = ecc_metadata
        kwargs["missing_value"] = missing_value
        kwargs["can_infer_time"] = can_infer_time

        # detect if the data can be written straight to a file without going through the full
        # encoding process, which can be very expensive for large data.
        path_allowed = (
            target is not None
            and target._name == "file"
            and not ecc_metadata
            and not mars_metadata
            and values is not None
            and template is not None
            and missing_value == 9999
            and not field_metadata
        )
        hints = {"path_allowed": path_allowed}

        if data is not None:
            from earthkit.data import Field
            from earthkit.data.data.wrappers import from_object

            if template_field is None:
                template_field = data if isinstance(data, Field) else None

            data = from_object(data)
            return data._encode(
                self,
                hints=hints,
                target=target,
                template=template,
                template_field=template_field,
                field_metadata=field_metadata,
                **kwargs,
            )
        else:
            new_handle = None
            if mars_metadata:
                try:
                    new_handle = handle_from_mars(values, mars_metadata)
                    if new_handle is not None:
                        if field_metadata or ecc_metadata:
                            values = None
                            template = new_handle
                            new_handle = None
                        else:
                            return GribEncodedData(new_handle, template_field=template_field)

                except Exception as e:
                    raise RuntimeError("Failed to create handle from mars metadata") from e

            handle = self._create_handle(
                template=template,
                values_shape=values.shape if values is not None else None,
                ecc_metadata=ecc_metadata,
                field_metadata=field_metadata,
            )
            new_handle = self._update_handle(handle, **kwargs)
            return GribEncodedData(new_handle, template_field=template_field)

    def _has_standard_date_input(self, d):
        for v in d:
            date = v.get("date", None)
            if isinstance(date, int):
                return True
            if isinstance(date, str) and len(date) == 8:
                return True

        return False

    def _check_grid_spec(self, handle, metadata):
        """Check and remove the gridSpec from metadata if needed.

        Parameters
        ----------
        handle : object
            The handle to check for grid type and name.
        metadata : dict
            The metadata dictionary from which to remove the gridSpec if the grid is unstructured.

        Returns
        -------
        None

        Notes
        -----
        This code handles the situation where both the handle and the gridSpec represent unstructured grids.
        The problem is that ecCodes does not allow setting a gridSpec of this type on a handle and raises
        an exception if attempted. This poses a problem when the handle and the gridSpec represent the same
        unstructured grid. In this case the gridSpec is not needed and has to be removed from the metadata to
        avoid problems and let the encoding process to proceed without conflicts. The code below uses very
        simple assumptions to detect this situation, which needs improvement.
        """
        try:
            grid_spec = metadata.get("gridSpec", None)
            if handle is None or grid_spec is None:
                return

            grid_type = handle.get("gridType", default=None)
            grid_name = handle.get("gridName", default=None)
            if grid_type is None or grid_name is None:
                return

            if grid_type == "unstructured_grid" and grid_name == "undefined":
                from eckit.geo import Grid

                grid = Grid(grid_spec)
                if grid.type in ["unstructured", "unstructured_ll"]:
                    metadata.pop("gridSpec", None)
        except Exception:
            pass

    def _encode(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_field(
        self, field, *, target=None, values=None, template=None, template_field=None, metadata=None, **kwargs
    ):
        # check if the field is already encoded in the desired format

        r = {}
        field._get_grib_context(r)

        handle = r.pop("handle", None)
        field_values = r.pop("values", None)

        self._check_grid_spec(handle, r)

        if r:
            self._update_metadata_from_field(field, r)
            if metadata is None:
                metadata = r
            else:
                r.update(metadata)
                metadata = r

        if field_values is None and values is None and template is None and not metadata:
            return GribEncodedData(handle, template_field=template_field)

        # set bitspervalue
        if "bitsPerValue" not in metadata:
            bpv = None
            field_md = field._get_grib()
            # If the Field grib metadata has an extra key "bitsPerValue", use it since it indicates that
            # the handle was deflated and the original bitsPerValue is not available from it.
            if field_md is not None:
                bpv = field_md.get_extra_key("bitsPerValue", default=None)
                if bpv is not None:
                    metadata["bitsPerValue"] = bpv
                else:
                    bpv = field_md.get("bitsPerValue", default=None)
                    if bpv is not None and bpv > 0:
                        metadata["bitsPerValue"] = bpv

        if values is None:
            values = field_values

        if values is None:
            values = field.values

        if template is None:
            template = handle

        handle = self._create_handle(
            values_shape=values.shape if values is not None else None, ecc_metadata=metadata, template=template
        )

        new_handle = self._update_handle(handle, values=values, metadata=metadata, **kwargs)

        return GribEncodedData(new_handle, template_field=template_field)

    def _encode_fieldlist(self, fs, *, target=None, **kwargs):
        for f in fs:
            yield f._encode(self, target=target, **kwargs)

    def _encode_xarray(self, data, *, target=None, **kwargs):
        accessor = data.earthkit
        return self._encode_fieldlist(accessor._generator(), target=target, **kwargs)

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info, *, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "grib"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None

    def _create_handle(self, template=None, values_shape=None, ecc_metadata=None, field_metadata=None):

        clone = True
        if template is None:
            template = self.template
            clone = False
        handle = handle_from_template(
            template=template, values_shape=values_shape, field_metadata=field_metadata, clone=clone
        )

        if handle is None:
            if values_shape is None:
                raise ValueError("No values to encode")
            if field_metadata:
                raise ValueError("Cannot provide field_metadata without a template or handle")
            handle = handle_from_metadata(values_shape, ecc_metadata, _COMPULSORY)

        return handle

    def _update_handle(
        self, handle, values=None, check_nans=True, metadata=None, missing_value=9999, can_infer_time=False
    ):
        if handle is None:
            raise ValueError("No handle to encode")

        # Make a copy as we may modify it
        if metadata is None:
            metadata = {}

        # compulsory = _COMPULSORY

        self._update_metadata(handle, metadata, can_infer_time)

        # right now the encoder is only able to write pv for edition 2
        if "pv" in metadata and metadata.get("edition", None) != 2:
            metadata["edition"] = 2

        # eccodes keys are order dependent
        KEY_ORDER = ("edition", "stepType")
        r = {k: metadata.pop(k) for k in KEY_ORDER if k in metadata}
        r.update(metadata)
        metadata = r

        if check_nans and values is not None:
            import numpy as np

            if np.isnan(values).any():
                # missing_value = np.finfo(values.dtype).max
                missing_value = missing_value
                values = np.nan_to_num(values, nan=missing_value)
                metadata["missingValue"] = missing_value
                metadata["bitmapPresent"] = 1

        if str(metadata.get("edition")) == "1":
            for k in _NOT_IN_EDITION_1:
                metadata.pop(k, None)

        if int(metadata.get("deleteLocalDefinition", 0)):
            for k in ("class", "type", "stream", "expver", "setLocalDefinition"):
                metadata.pop(k, None)

        # keep the original generatingProcessIdentifier if not set
        if "generatingProcessIdentifier" in metadata:
            if metadata["generatingProcessIdentifier"] is None:
                metadata.pop("generatingProcessIdentifier")

        # # TODO: revisit that logic
        # if "generatingProcessIdentifier" not in metadata:
        #     metadata["generatingProcessIdentifier"] = 255
        # else:
        #     # kee
        #     if metadata["generatingProcessIdentifier"] is None:
        #         metadata.pop("generatingProcessIdentifier")

        LOG.debug("GribOutput.metadata %s", metadata)

        single = {}
        multiple = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float, str, bool)):
                single[k] = v
            else:
                multiple[k] = v

        if len(single) == 1:
            # if there is only one key, set it directly to avoid the overhead of set_multiple
            k, v = next(iter(single.items()))
            handle.set(k, v)
            single = {}
        elif len(single) > 1:
            try:
                # Try to set all metadata at once
                # This is needed when we set multiple keys that are interdependent
                handle.set_multiple(single)
            except Exception as e:
                LOG.warning("Failed to set metadata at once: %s", e)
                # Try again, but one by one
                for k, v in single.items():
                    handle.set(k, v)

        for k, v in multiple.items():
            handle.set(k, v)

        if values is not None:
            handle.set_values(values)

        return handle

    def _update_metadata_from_field(self, field, metadata):
        if "stepRange" in metadata:
            step_range = metadata["stepRange"]
            if isinstance(step_range, datetime.timedelta):
                step = field.step
                start = step - step_range
                end = step
                metadata["stepRange"] = step_range_to_grib(start, end)

    def _update_metadata(self, handle, metadata, can_infer_time):
        # TODO: revisit the logic
        combined = Combined(handle, metadata)

        if "stepRange" in metadata:
            step_range = metadata["stepRange"]
            if isinstance(step_range, datetime.timedelta):
                start_step, end_step = step_range.split("-")
                metadata["startStep"] = int(start_step)
                metadata["endStep"] = int(end_step)
                del metadata["stepRange"]
            else:
                metadata["startStep"] = int(step_range)
                metadata["endStep"] = int(step_range)
                del metadata["stepRange"]

        if "step" in metadata or "endStep" in metadata:
            if combined["type"] == "an":
                metadata["type"] = "fc"

        if "time" in metadata:  # TODO, use a normaliser
            try:
                time = int(metadata["time"])
                if time < 100:
                    metadata["time"] = time * 100
            except ValueError:
                pass

        if "time" not in metadata and "date" in metadata and can_infer_time:
            if isinstance(metadata["date"], datetime.datetime):
                date = metadata["date"]
                metadata["time"] = date.hour * 100 + date.minute

        if "date" in metadata:
            if isinstance(metadata["date"], datetime.datetime):
                date = metadata["date"]
                metadata["date"] = date.year * 10000 + date.month * 100 + date.day
            else:
                metadata["date"] = int(metadata["date"])

        if "stream" not in metadata:
            if "number" in metadata:
                metadata["stream"] = "enfo"
                metadata.setdefault("type", "pf")

        if "number" in metadata:
            metadata.setdefault("productDefinitionTemplateNumber", 1)  # 11 for accumulations

        if metadata.get("type") in ("pf", "cf"):
            metadata.setdefault("typeOfGeneratingProcess", 4)

        if "param" in metadata:
            param = metadata.pop("param")
            try:
                metadata["paramId"] = int(param)
            except ValueError:
                metadata["shortName"] = param

        if "levtype" in metadata:
            import warnings

            warnings.warn(
                "The 'levtype' ecCodes key is deprecated in the GribEncoder. It has been "
                "read-only since ecCodes 2.33.0 and its use is discouraged. Use 'typeOfLevel' instead. "
                "For backwards compatibility, the values 'sfc', 'pl', 'ml', 'pt', and "
                "'pv' are still accepted and silently mapped to the equivalent 'typeOfLevel' value, "
                "but this mapping will be removed in a future release.",
                DeprecationWarning,
            )

            # levtype is a readOnly key in ecCodes >= 2.33.0
            levtype_remap = {
                "pl": "isobaricInhPa",
                "ml": "hybrid",
                "pt": "theta",
                "pv": "potentialVorticity",
                "sfc": "surface",
            }

            levtype = metadata.pop("levtype")
            type_of_level = metadata.get("typeOfLevel")

            if levtype in levtype_remap:
                if type_of_level is None:
                    metadata["typeOfLevel"] = levtype_remap[levtype]
                elif type_of_level != levtype_remap[levtype]:
                    raise ValueError(
                        f"Cannot set levtype='{levtype}': typeOfLevel='{type_of_level}' is already set "
                        f"to an incompatible value. Use typeOfLevel exclusively; levtype is deprecated "
                        "and has been read-only since ecCodes 2.33.0."
                    )

            else:
                raise ValueError(
                    f"Unsupported levtype='{levtype}'. "
                    "Use typeOfLevel exclusively; levtype is deprecated and has been read-only since ecCodes 2.33.0. "
                    "For backwards compatibility, the following levtype values are still "
                    f"accepted: {list(levtype_remap)}."
                )
