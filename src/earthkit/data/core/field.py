# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import warnings
from collections import defaultdict

import deprecation
from earthkit.utils.array import array_namespace as eku_array_namespace
from earthkit.utils.array import convert as convert_array
from earthkit.utils.array.convert import convert_dtype

from earthkit.data.core import Base
from earthkit.data.core.order import Patch
from earthkit.data.core.order import Remapping
from earthkit.data.core.order import build_remapping
from earthkit.data.decorators import normalize
from earthkit.data.field.data import DataFieldPart
from earthkit.data.field.ensemble import EnsembleFieldPartHandler
from earthkit.data.field.geography import GeographyFieldPartHandler
from earthkit.data.field.labels import SimpleLabels
from earthkit.data.field.parameter import ParameterFieldPartHandler
from earthkit.data.field.proc import ProcFieldPartHandler
from earthkit.data.field.time import TimeFieldPartHandler
from earthkit.data.field.vertical import VerticalFieldPartHandler
from earthkit.data.indexing.simple import SimpleFieldList
from earthkit.data.utils.array import flatten as array_flatten
from earthkit.data.utils.array import reshape as array_reshape
from earthkit.data.utils.array import target_shape
from earthkit.data.utils.compute import wrap_maths
from earthkit.data.utils.metadata.args import metadata_argument
from earthkit.data.utils.metadata.args import metadata_argument_new

GRIB = "grib"

LS_KEYS = [
    "variable",
    "valid_datetime",
    "base_datetime",
    "step",
    "level",
    "vertical_type",
    "member",
    "grid_type",
]


# Define field part names. These are also namespace names.
DATA = "data"
TIME = "time"
PARAMETER = "parameter"
GEOGRAPHY = "geography"
VERTICAL = "vertical"
ENSEMBLE = "ensemble"
PROC = "proc"
LABELS = "labels"
METADATA = "metadata"

DUMP_ORDER = [
    PARAMETER,
    TIME,
    VERTICAL,
    ENSEMBLE,
    GEOGRAPHY,
]


@wrap_maths
class Field(Base):
    """A class to represent a field in Earthkit.

    A field in Earthkit is a horizontal slice of the atmosphere/hydrosphere at
    a given time.

    A Field object is composed of several parts:

    - data: the data values of the field
    - time: the time of the field
    - parameter: the parameter of the field
    - geography: the geography of the field
    - vertical: the vertical level of the field
    - ensemble: the ensemble specification of the field
    - proc: the processing specification of the field
    - labels: the labels of the field

    Field is not polymorphic, but its parts are.

    To create a new Field object use the factory methods such as :meth:`from_dict`
    or :meth:`from_parts`.

    Parameters
    ----------
    data : DataFieldPart
        The data of the field.
    time : TimeFieldPart
        The time of the field.
    parameter : ParameterFieldPart
        The parameter of the field.
    geography : GeographyFieldPart
        The geography of the field.
    vertical : VerticalFieldPart
        The vertical level of the field.
    ensemble : EnsembleFieldPartHandler
        The ensemble specification of the field.
    proc : ProcFieldPart
        The processing specification of the field.
    labels : SimpleLabels
        The labels of the field.
    **kwargs : dict
        Other keyword arguments to be passed to the Field constructor.
        These can include metadata, such as `ls_keys` for GRIB fields.

    """

    _PART_NAMES = (
        DATA,
        TIME,
        PARAMETER,
        GEOGRAPHY,
        VERTICAL,
        ENSEMBLE,
        PROC,
        LABELS,
    )

    _DEFAULT_PART_CLS = {
        DATA: DataFieldPart,
        TIME: TimeFieldPartHandler,
        PARAMETER: ParameterFieldPartHandler,
        GEOGRAPHY: GeographyFieldPartHandler,
        VERTICAL: VerticalFieldPartHandler,
        ENSEMBLE: EnsembleFieldPartHandler,
        PROC: ProcFieldPartHandler,
        LABELS: SimpleLabels,
    }

    # this will be initialized by the init_part_conf decorator
    # _PART_KEYS = None

    def __init__(
        self,
        *,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):

        if labels is None:
            labels = SimpleLabels()

        self._parts = {
            DATA: data,
            TIME: time,
            PARAMETER: parameter,
            GEOGRAPHY: geography,
            VERTICAL: vertical,
            ENSEMBLE: ensemble,
            PROC: proc,
            LABELS: labels,
        }

        self._private = dict()

    @classmethod
    def from_field(
        cls,
        field,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        r"""Create a Field object from another Field object.

        Parameters
        ----------
        field : Field
            The field to copy from.
        data : DataFieldPart, dict or None
            The data of the field. When specified it is used instead of the data in
            the ``field``.
        time : Time, TimeFieldPart, dict or None
            The time of the field. When specified it is used instead of the time
            part in the ``field``.
        parameter : Parameter, ParameterFieldPart, dict or None
            The parameter of the field. When specified it is used instead of the
            parameter part in the ``field``.
        geography : Geography, GeographyFieldPart, dict or None
            The geography of the field. When specified it is used instead of the geography
            part in the ``field``.
        vertical : Vertical, VerticalFieldPart, dict or None
            The vertical level of the field. When specified it is used instead of the
            vertical part in the ``field``.
        ensemble : Ensemble, EnsembleFieldPart, dict or None
            The ensemble specification of the field. When specified it is used instead of
            the ensemble part in the ``field``.
        proc :  Proc, ProcFieldPart, dict or None
            The processing specification of the field. When specified it is used instead of
            the processing part in the ``field``.
        labels : SimpleLabels, dict or None
            The labels of the field. When specified it is used instead of the labels
            in the ``field``.

        Returns
        -------
        Field
            A new Field object with the parts copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            DATA: data,
            TIME: time,
            PARAMETER: parameter,
            GEOGRAPHY: geography,
            VERTICAL: vertical,
            ENSEMBLE: ensemble,
            PROC: proc,
            LABELS: labels,
        }

        for name in Field._PART_NAMES:
            v = _kwargs[name]
            if v is not None:
                _kwargs[name] = Field._DEFAULT_PART_CLS[name].from_any(v)
            else:
                _kwargs[name] = field._parts[name]

        r = field.__class__(**_kwargs)

        # copy private data and initialize
        if field._private:
            r._private = field._private.copy()
            for v in r._private.values():
                if hasattr(v, "sync"):
                    v.sync(r)
        return r

    @classmethod
    def from_dict(cls, d):
        r"""Create a Field object from a dictionary.

        Parameters
        ----------
        d : dict
            The dictionary to create the Field from. Keys not used by any part
            are added to the labels.

        Returns
        -------
        Field
            A new Field object created from the dictionary.
        """
        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")

        parts = {}
        d = d.copy()

        # TODO: add support for proc part

        shape_hint = None

        if "values" in d:
            values = d.pop("values")
            parts[DATA] = cls._DEFAULT_PART_CLS[DATA].from_dict({"values": values})
            shape_hint = parts[DATA].get_values(copy=False).shape

        for name in [TIME, PARAMETER, VERTICAL, ENSEMBLE, GEOGRAPHY]:
            d_part = {}
            for k in list(d.keys()):
                if k.startswith(name + "."):
                    d_part[k.split(".", 1)[1]] = d.pop(k)

            # geography may need shape hint from data so handled separately
            if name == GEOGRAPHY:
                parts[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_part, shape_hint=shape_hint)
            else:
                parts[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_part)

        # geography may need shape hint from data so handled separately
        shape_hint = None
        if parts.get(DATA):
            shape_hint = parts[DATA].get_values(copy=False).shape

        # d_part = {k.split(".")[1]: v for k, v in d.items() if k.startswith(GEOGRAPHY + ".")}
        # parts[GEOGRAPHY] = cls._DEFAULT_PART_CLS[GEOGRAPHY].from_dict(d, shape_hint=shape_hint)

        # the unused items are added as labels
        labels = SimpleLabels(d)

        return cls(**parts, labels=labels)

    @classmethod
    def from_parts(
        cls,
        data=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        r"""Create a Field object from parts.

        Parameters
        ----------
        data : DataFieldPart, dict
            The data of the field.
        time : Time, TimeFieldPart, dict
            The time of the field.
        parameter : Parameter, ParameterFieldPart, dict
            parameter part in the ``field``.
        geography : Geography, GeographyFieldPart, dict or None
            The geography of the field.
        vertical : Vertical, VerticalFieldPart, dict or None
            The vertical level of the field.
        ensemble : Ensemble, EnsembleFieldPart, dict or None
            The ensemble specification of the field.
        proc :  Proc, ProcFieldPart, dict or None
            The processing specification of the field.
        labels : SimpleLabels, dict or None
            The labels of the field.

        Returns
        -------
        Field
            A new Field object with the parts copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            DATA: data,
            TIME: time,
            PARAMETER: parameter,
            VERTICAL: vertical,
            ENSEMBLE: ensemble,
            PROC: proc,
            LABELS: labels,
        }

        parts = {}

        for name, v in _kwargs.items():
            if v is not None:
                part = cls._DEFAULT_PART_CLS[name].from_any(v, dict_kwargs={"allow_unused": True})
                parts[name] = part

        if isinstance(geography, dict):
            shape_hint = None
            if "data" in parts:
                data = parts["data"]
                shape_hint = data.values.shape
            parts[GEOGRAPHY] = cls._DEFAULT_PART_CLS[GEOGRAPHY].from_dict(
                allow_unused=True, shape_hint=shape_hint
            )
        elif geography is not None:
            parts[GEOGRAPHY] = cls._DEFAULT_PART_CLS[GEOGRAPHY].from_any(geography)

        return cls(**parts)

    @property
    def ensemble(self):
        """Ensemble: Return the ensemble specification of the field."""
        return self._parts[ENSEMBLE].part

    @property
    def time(self):
        """Time: Return the time specification of the field."""
        return self._parts[TIME].part

    @property
    def vertical(self):
        """Vertical: Return the vertical specification of the field."""
        return self._parts[VERTICAL].part

    @property
    def parameter(self):
        """Parameter: Return the vertical specification of the field."""
        return self._parts[PARAMETER].part

    @property
    def geography(self):
        """Geography: Return the geography specification of the field."""
        return self._parts[GEOGRAPHY].part

    @property
    def proc(self):
        """Proc: Return the proc specification of the field."""
        return self._parts[PROC].part

    @property
    def labels(self):
        """SimpleLabels: Return the labels of the field."""
        return self._parts[LABELS]

    @classmethod
    def from_array(cls, array):
        return cls.from_dict({"values": array})

    @property
    @deprecation.deprecated(deprecated_in="0.19.0", details="Use array_namespace instead")
    def array_backend(self):
        r""":obj:`ArrayBackend`: Return the array namespace of the field."""
        return self.array_namespace

    @property
    def array_namespace(self):
        r""":obj:`ArrayBackend`: Return the array namespace of the field."""
        return eku_array_namespace(self.values)

    def free(self):
        self._parts[DATA] = self._parts[DATA].Offloader(self._parts[DATA])

    @property
    def values(self):
        """array-like: Return the values of the field."""
        return self._parts[DATA].values

    @property
    def shape(self):
        if self._parts.get(GEOGRAPHY):
            return self._parts[GEOGRAPHY].part.shape()
        else:
            return self.values.shape

    def to_numpy(self, flatten=False, dtype=None, copy=True, index=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: ndarray indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        ndarray
            Field values

        """
        v = self._parts[DATA].get_values(dtype=dtype, copy=copy)
        v = convert_array(v, array_namespace="numpy")
        v = array_flatten(v) if flatten else array_reshape(v, self.shape)

        if index is not None:
            v = v[index]

        return v

    def to_array(
        self,
        flatten=False,
        dtype=None,
        copy=True,
        array_backend=None,
        array_namespace=None,
        device=None,
        index=None,
    ):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, array_namespace or None
            The array namespace to be used. When it is :obj:`None` the underlying array format
            of the field is used. **Deprecated since version 0.19.0**. Use ``array_namespace`` instead.
            In versions before 0.19.0 an :obj:`ArrayBackend` was also accepted here, which is no longer
            the case.
        array_namespace: str, array_namespace or None
            The array namespace to be used. When it is :obj:`None` the underlying array format
            of the field is used. **New in version 0.19.0**.
        device: str or None
            The device where the array will be allocated. When it is :obj:`None` the default device is used.
        index: array indexing object, optional
            The index of the values and to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        array-array
            Field values.

        """
        if array_backend is not None:
            warnings.warn(
                "to_array(): 'array_backend' is deprecated. Use 'array_namespace' instead", DeprecationWarning
            )
            if array_namespace is not None:
                raise ValueError("to_array(): only one of array_backend and array_namespace can be specified")
            array_namespace = array_backend

        v = self._parts[DATA].get_values(dtype=dtype, copy=copy)
        if array_namespace is not None:
            v = convert_array(v, array_namespace=array_namespace, device=device)

        v = array_flatten(v) if flatten else array_reshape(v, self.shape)
        if index is not None:
            v = v[index]

        return v

    def _get_part(self, key):
        """Return the part name, part object and key name for the specified key."""
        # m = self._PART_KEYS.get(key)

        m = None
        if m is not None:
            return m[0], self._parts.get(m[0]), m[1]
        if "." in key:
            part, name = key.split(".", 1)
            if part in self._parts:
                return part, self._parts.get(part), name
            return part, None, name
        elif key in self._parts[DATA]:
            return DATA, self._parts.get(DATA), key
        return None, None, None

        # if "." in key:
        #     part, name = key.split(".", 1)
        #     return part, self._parts.get(part), name
        # else:
        #     for part, d in self._parts.items():
        #         if key in d.ALL_KEYS:
        #             return part, d, key

        # return None, None, None

    def _get_single(
        self, key, default=None, *, astype=None, raise_on_missing=False, remapping=None, patches=None
    ):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Specify the metadata key to extract.
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found and raise_on_missing is ``False``.
        astype: type as str, int or float
            Return type for ``key``. When it is supported ``astype`` is passed to the
            underlying accessor as an option. Otherwise the value is
            cast to ``astype`` after it is taken from the accessor.
        raise_on_missing: bool
            When True, raises KeyError if ``key`` is not found.

        Returns
        -------
        value
            Returns the ``key`` value. Returns ``default`` if ``key`` is not found
            and ``raise_on_missing`` is False.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and ``key`` is not found.

        """
        remapping = build_remapping(remapping, patches, forced_build=False)
        if remapping:
            return remapping(self.get_single)(
                key, default=default, astype=astype, raise_on_missing=raise_on_missing
            )

        part_name, part, key_name = self._get_part(key)

        if part:
            return part.get(key_name, default=default, astype=astype, raise_on_missing=raise_on_missing)

        if not part_name:
            from earthkit.data.core.config import CONFIG

            if CONFIG.get("search_all_field_parts", True):
                part_name = METADATA

        if part_name == METADATA:
            for _, private_part in self._private.items():
                if hasattr(private_part, "metadata"):
                    return private_part.metadata(
                        key_name, default=default, astype=astype, raise_on_missing=raise_on_missing
                    )
                else:

                    def _cast(v):
                        if callable(astype):
                            try:
                                return astype(v)
                            except Exception:
                                return None
                        return v

                    # TODO: review this
                    v = self.private_part.get(key)
                    if v is not None:
                        return _cast(v)

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in field")

        return default

    def _get_fast(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output=None,
        remapping=None,
        joiner=None,
    ):
        r"""Fast implementation of :meth:`get` for internal use.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. When ``default`` is a single
            value, it is used for all the keys. Otherwise it must be a list/tuple of the
            same length as ``keys``.
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.
        output: type, None
            The output type. Can be:

            - None: when ``keys`` is a str returns a single value, when ``keys`` is a list/tuple
                returns a list/tuple of values
            - list/tuple: returns a list/tuple of values. In this case ``keys`` must be a list/tuple.
            - dict: returns a dictionary with keys and their values.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list/tuple of values when ``output``
              is None, list or tuple
            - when ``output`` is dict returns dictionary with keys and their values


        Notes
        -----
        This method assumes that the arguments have been normalized e.g. by using
        :func:`metadata_argument_new`. No checks are performed on the arguments to
        ensure that they are valid and consistent.
        """
        meth = self._get_single
        # Remapping must be an object if defined
        if remapping is not None:
            assert isinstance(remapping, (Remapping, Patch))
            meth = remapping(meth, joiner=joiner)

        if isinstance(keys, str):
            r = meth(keys, default=default, astype=astype, raise_on_missing=raise_on_missing)
            return r if output is not dict else {keys: r}
        elif isinstance(keys, (list, tuple)):
            if output is not dict:
                r = [
                    meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                ]
                return r if output is list else tuple(r)
            else:
                return {
                    k: meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                }

    def get(
        self,
        keys,
        default=None,
        *,
        astype=None,
        raise_on_missing=False,
        output=None,
        remapping=None,
        patches=None,
    ):
        r"""Return the values for the specified keys.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. When ``default`` is a single
            value, it is used for all the keys. Otherwise it must be a list/tuple of the
            same length as ``keys``.
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.
        output: type, None
            When None (default) returns the same type as that of ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list of values

            When ``output`` is dict, returns a dictionary with keys and their values.
            Other types are not supported.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list/tuple of values
            - when ``output`` is dict returns dictionary with keys and their values.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.

        """
        if not keys:
            raise ValueError("At least one key must be specified.")

        keys, astype, default, keys_arg_type = metadata_argument_new(
            keys,
            default=default,
            astype=astype,
        )

        if output is None:
            if keys_arg_type is not str:
                output = keys_arg_type
        elif output is not dict:
            raise ValueError("output must be None or dict")

        remapping = build_remapping(remapping, patches, forced_build=False)

        r = self._get_fast(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            remapping=remapping,
            output=output,
        )

        return r

    def metadata(
        self,
        keys,
        default=None,
        *,
        astype=None,
        raise_on_missing=False,
        output=None,
        remapping=None,
        patches=None,
    ):

        if isinstance(keys, str):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys]
            if is_tuple:
                keys = tuple(keys)

        return self.get(
            keys,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            output=output,
            remapping=remapping,
            patches=patches,
        )

    def metadata_ori(self, *keys, astype=None, remapping=None, patches=None, **kwargs):
        r"""Return metadata values from the field.

        When called without any arguments returns a :obj:`Metadata` object.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying metadata keys. Can be empty, in this case all
            the keys from the specified ``namespace`` will
            be used. (See examples below).
        astype: type name, :obj:`list` or :obj:`tuple`
            Return types for ``keys``. A single value is accepted and applied to all the ``keys``.
            Otherwise, must have same the number of elements as ``keys``. Only used when
            ``keys`` is not empty.
        remapping: dict, optional
            Creates new metadata keys from existing ones that we can refer to in ``*args`` and
            ``**kwargs``. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}
        **kwargs: dict, optional
            Other keyword arguments:

            * namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
                The namespace to choose the ``keys`` from. When ``keys`` is empty and ``namespace`` is
                :obj:`all` all the available namespaces will be used. When ``keys`` is non empty
                ``namespace`` cannot specify multiple values and it cannot be :obj:`all`. When
                ``namespace`` is None or empty str all the available keys will be used
                (without a namespace qualifier).

            * default: value, optional
                Specifies the same default value for all the ``keys`` specified. When ``default`` is
                **not present** and a key is not found or its value is a missing value
                :obj:`metadata` will raise KeyError.

        Returns
        -------
        single value, :obj:`list`, :obj:`tuple`, :obj:`dict` or :obj:`Metadata`
            - when called without any arguments returns a :obj:`Metadata` object
            - when ``keys`` is not empty:
                - returns single value when ``keys`` is a str
                - otherwise returns the same type as that of ``keys`` (:obj:`list` or :obj:`tuple`)
            - when ``keys`` is empty:
                - when ``namespace`` is None or an empty str returns a :obj:`dict` with all
                  the available keys and values
                - when ``namespace`` is :obj:`str` returns a :obj:`dict` with the keys and values
                  in that namespace
                - otherwise returns a :obj:`dict` with one item per namespace (dict of dict)

        Raises
        ------
        KeyError
            If no ``default`` is set and a key is not found in the message or it has a missing value.

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")

        Calling without arguments:

        >>> r = ds[0].metadata()
        >>> r
        <earthkit.data.readers.grib.metadata.GribMetadata object at 0x164ace170>
        >>> r["name"]
        '2 metre temperature'

        Getting keys with their native type:

        >>> ds[0].metadata("param")
        '2t'
        >>> ds[0].metadata("param", "units")
        ('2t', 'K')
        >>> ds[0].metadata(("param", "units"))
        ('2t', 'K')
        >>> ds[0].metadata(["param", "units"])
        ['2t', 'K']
        >>> ds[0].metadata(["param"])
        ['2t']
        >>> ds[0].metadata("badkey")
        KeyError: 'badkey'
        >>> ds[0].metadata("badkey", default=None)
        <BLANKLINE>

        Prescribing key types:

        >>> ds[0].metadata("centre", astype=int)
        98
        >>> ds[0].metadata(["paramId", "centre"], astype=int)
        [167, 98]
        >>> ds[0].metadata(["centre", "centre"], astype=[int, str])
        [98, 'ecmf']

        Using namespaces:

        >>> ds[0].metadata(namespace="parameter")
        {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature', 'shortName': '2t'}
        >>> ds[0].metadata(namespace=["parameter", "vertical"])
        {'parameter': {'centre': 'ecmf', 'paramId': 167, 'units': 'K', 'name': '2 metre temperature',
         'shortName': '2t'},
         'vertical': {'typeOfLevel': 'surface', 'level': 0}}
        >>> r = ds[0].metadata(namespace=all)
        >>> r.keys()
        dict_keys(['default', 'ls', 'geography', 'mars', 'parameter', 'statistics', 'time', 'vertical'])
        >>> r = ds[0].metadata(namespace=None)
        >>> len(r)
        186
        >>> r["name"]
        '2 metre temperature'
        """

        if remapping is not None or patches is not None:
            from earthkit.data.core.order import build_remapping

            remapping = build_remapping(remapping, patches)
            return remapping(self.metadata)(*keys, astype=astype, **kwargs)

        # when called without arguments returns the metadata object
        if len(keys) == 0 and astype is None and not kwargs:
            raise NotImplementedError("Field.metadata() without arguments is not implemented. ")
            # return self._metadata

        namespace = kwargs.pop("namespace", None)
        key, namespace, astype, key_arg_type = metadata_argument(*keys, namespace=namespace, astype=astype)

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            if namespace and namespace[0] != "default":
                key = [namespace[0] + "." + k for k in key]

            raise_on_missing = "default" not in kwargs
            default = kwargs.pop("default", None)

            r = [
                self.get(
                    k,
                    default=default,
                    astype=kt,
                    raise_on_missing=raise_on_missing,
                    **kwargs,
                )
                for k, kt in zip(key, astype)
            ]

            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
                return tuple(r)
            else:
                return r
        elif namespace:
            if all in namespace:
                namespace = self._metadata.namespaces()

            r = {ns: self._metadata.as_namespace(ns) for ns in namespace}
            if len(r) == 1:
                return r[namespace[0]]
            else:
                return r
        else:
            return self._metadata.as_namespace(None)

    def set(self, *args, **kwargs):
        # collect keys to set per part

        kwargs = kwargs.copy()

        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                kwargs.update(a)
                continue
            raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

        _kwargs = defaultdict(dict)
        for k, v in kwargs.items():
            part_name, part, key_name = self._get_part(k)
            if part is not None:
                if key_name is not None and key_name != "":
                    _kwargs[part_name][key_name] = v
                else:
                    raise KeyError(f"Key {k} cannot be set on the field.")
            else:
                raise KeyError(f"Key {k} cannot be set on the field.")
            # else:
            #     _kwargs[LABELS][k] = v

        if _kwargs:
            r = {}
            for part_name, v in _kwargs.items():
                part = self._parts[part_name]
                s = part.set(**v)
                r[part_name] = s

            if r:
                return Field.from_field(self, **r)
            else:
                raise ValueError("No valid keys to set in the field.")
        return None

    def _set_values(self, array):
        data = self._parts[DATA].set_values(array)
        return Field.from_field(self, data=data)

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def save(self, filename, append=False, **kwargs):
        r"""Write the field into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.
        """
        metadata = kwargs.pop("metadata", None)
        if metadata is None:
            metadata = {}
            bits_per_value = kwargs.pop("bits_per_value", None)
            if bits_per_value is not None:
                metadata = {"bitsPerValue": bits_per_value}
            # metadata, kwargs = _bits_per_value_to_metadata(**kwargs)
        self.to_target("file", filename, append=append, metadata=metadata, **kwargs)
        # the original implementation
        # flag = "wb" if not append else "ab"
        # with open(filename, flag) as f:
        #     self.write(f, **kwargs)

    @deprecation.deprecated(deprecated_in="0.13.0", details="Use to_target() instead")
    def write(self, f, **kwargs):
        metadata = kwargs.pop("metadata", None)
        if metadata is None:
            metadata = {}
            bits_per_value = kwargs.pop("bits_per_value", None)
            if bits_per_value is not None:
                metadata = {"bitsPerValue": bits_per_value}
            # metadata, kwargs = _bits_per_value_to_metadata(**kwargs)
        self.to_target("file", f, metadata=metadata, **kwargs)

    def to_target(self, target, *args, **kwargs):
        r"""Write the field into a target object.

        Parameters
        ----------
        target: object
            The target object to write the field into.
        *args: tuple
            Positional arguments used to specify the target object.
        **kwargs: dict, optional
            Other keyword arguments used to write the field into the target object.
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def default_encoder(self):
        # TODO: improve this to support more formats and to be more robust
        if self._private and "metadata" in self._private:
            if hasattr(self._private["metadata"], "NAME") and self._private["metadata"].NAME == "grib":
                return "grib"
        return "dict"

    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        return encoder._encode_field(self, **kwargs)

    def to_field(self, array=True):
        """Return the field itself."""
        return self

    def to_array_field(self, array_namespace=None, device=None, flatten=False, dtype=None):
        grib = self.get_private_data("grib")
        if grib is not None:
            return grib.new_array_field(
                self, array_namespace=array_namespace, device=device, flatten=flatten, dtype=dtype
            )
        return self

    def to_fieldlist(self, fields=None):
        if fields is None:
            fields = [self]
        return SimpleFieldList.from_fields(fields)

    def to_xarray(self, *args, **kwargs):
        """Convert the Field into an Xarray Dataset.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.to_xarray`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.to_xarray`.

        Returns
        -------
        Xarray Dataset

        """
        return self.to_fieldlist().to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        pass

    def _namespace(self, name="all", *, namespace=None, simplify=True):
        r"""Return the namespaces as a dict.

        Parameters
        ----------
        name: :obj:`str`, :obj:`list`, :obj:`tuple` or :obj:`all`
            The namespaces to return. If `name` is :obj:`all`, None or empty str
            all the namespaces will be used.

        Returns
        -------
        dict
            Each namespace is represented as a dict. When ``simplify`` is True and
            ``name`` is a str and only one namespace is available the returned dict
            contains the keys and values of that namespace. Otherwise the returned
            dict contains one item per namespace.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        See Also
        --------
        dump

        """
        if name is None or name == "":
            raise ValueError("namespace(): name cannot be None or empty str. Use 'all' instead.")

        if name in ["all", all, ["all"], [all]]:
            name = None

        result = {}
        for m in self._parts.values():
            m.namespace(self, name, result)

        if name == "metadata" and self._private:
            md = self._private.get("metadata")

            if md and hasattr(md, "namespace"):
                md.namespace(self, namespace, result)

        # if (
        #     name is not None
        #     and not (isinstance(name, (list, tuple)) and len(name) == len(result))
        #     and self._private
        # ):
        #     for _, v in self._private.items():
        #         if hasattr(v, "namespace"):
        #             v.namespace(self, name, result)

        if simplify and isinstance(name, str) and len(result) == 1 and name in result:
            return result[name]

        return result

    def dump(self, part=all, filter=None, **kwargs):
        r"""Generate dump with all the metadata keys belonging to ``namespace``.

        In a Jupyter notebook it is represented as a tabbed interface.

        Parameters
        ----------
        namespace: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
            The namespace to dump. The following `namespace` values
            have a special meaning:

            - :obj:`all`: all the available namespaces will be used.
            - None or empty str: all the available keys will be used
                (without a namespace qualifier)

        **kwargs: dict, optional
            Other keyword arguments used for testing only

        Returns
        -------
        NamespaceDump
            Dict-like object with one item per namespace. In a Jupyter notebook represented
            as a tabbed interface to browse the dump contents.

        Examples
        --------
        :ref:`/examples/grib_metadata.ipynb`

        See Also
        --------
        namespace

        """
        from earthkit.data.utils.summary import format_namespace_dump

        d = self._namespace(part, namespace=filter, simplify=False)

        d1 = {}
        for k in DUMP_ORDER:
            if k in d:
                d1[k] = d.pop(k)

        d1.update(d)
        d = d1

        r = []
        for ns, v in d1.items():
            # v = self.as_namespace(ns)
            if v:
                r.append(
                    {
                        "title": ns if ns else "default",
                        "data": v,
                        "tooltip": f"Keys in the {ns} namespace",
                    }
                )

        return format_namespace_dump(r, selected="parameter", details=self.__class__.__name__, **kwargs)

    @property
    def default_ls_keys(self):
        return LS_KEYS

    def ls(self, *args, **kwargs):
        r"""Generate a list-like summary using a set of metadata keys.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.ls`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.ls`.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row.

        """
        return self.to_fieldlist().ls(*args, **kwargs)

    def head(self, *args, **kwargs):
        r"""Generate a head summary of the Field."""
        return self.to_fieldlist().head(*args, **kwargs)

    def tail(self, *args, **kwargs):
        r"""Generate a tail summary of the Field."""
        return self.to_fieldlist().tail(*args, **kwargs)

    def describe(self, *args, **kwargs):
        r"""Generate a summary of the Field."""
        return self.to_fieldlist().describe(*args, **kwargs)

    def _set_private_data(self, name, data):
        self._private[name] = data

    def get_private_data(self, name):
        return self._private.get(name)

    def _check(self):
        return
        # for m in self._parts.values():
        #     m.check(self)

    def _get_grib_context(self, context):
        grib = self.get_private_data("grib")
        if grib is not None:
            context["handle"] = grib.handle

        for m in self._parts.values():
            m.get_grib_context(context)

    @normalize("time.valid_datetime", "date")
    @normalize("time.base_datetime", "date")
    @normalize("time.forecast_reference_time", "date")
    @normalize("time.step", "timedelta")
    @staticmethod
    def normalise_key_values(**kwargs):
        r"""Normalise the selection input for :meth:`FieldList.sel`."""
        return kwargs

    def data(self, keys=("lat", "lon", "value"), flatten=False, dtype=None, index=None):
        r"""Return the values and/or the geographical coordinates for each grid point.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True a flat array per key is returned. Otherwise an array with the field's
            :obj:`shape` is returned for each key.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        index: array indexing object, optional
            The index of the values and or the latitudes/longitudes to be extracted. When it
            is None all the values and/or coordinates are extracted.

        Returns
        -------
        array-like
            An multi-dimensional array containing one array per key is returned
            (following the order in ``keys``). The underlying array format
            of the field is used. When ``keys`` is a single value only the
            array belonging to the key is returned.

        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> d = ds[0].data()
        >>> d.shape
        (3, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2, 0, 0]  # first value
        272.56417847
        >>> d = ds[0].data(keys="lon")
        >>> d.shape
        (7, 12)
        >>> d[0, 0]  # first longitude
        0.0

        See Also
        --------
        to_latlon
        to_points
        to_numpy
        values

        """
        _keys = dict(
            lat=self.geography.latitudes(),
            lon=self.geography.longitudes(),
            value=self.values,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        def _reshape(v, flatten):
            shape = target_shape(v, flatten, self.shape)
            return array_reshape(v, shape)

        r = {}
        for k in keys:
            # TODO: convert dtype
            # v = _keys[k](dtype=dtype)
            v = _keys[k]
            if v is None:
                raise ValueError(f"data: {k} not available")
            v = _reshape(v, flatten)
            if index is not None:
                v = v[index]
            r[k] = v

        # convert latlon to array format
        ll = {k: r[k] for k in r if k != "value"}
        if ll:
            sample = r.get("value", None)
            if sample is None:
                sample = self._parts[DATA].get_values(dtype=dtype)
            target_xp = eku_array_namespace(sample)
            device = target_xp.device(sample)
            target_dtype = None
            if dtype is not None:
                target_dtype = convert_dtype(dtype, target_xp)

            for k, v in ll.items():
                r[k] = convert_array(v, array_namespace=target_xp, device=device)
                if target_dtype is not None:
                    r[k] = target_xp.astype(r[k], target_dtype, copy=False)

        r = list(r.values())
        if len(r) == 1:
            return r[0]
        else:
            return eku_array_namespace(r[0]).stack(r)

    def to_latlon(self, flatten=False, dtype=None, index=None):
        r"""Return the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
            longitudes, respectively. The underlying array format
            of the field is used.

        See Also
        --------
        to_points

        """
        lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
        return dict(lat=lat, lon=lon)

    def to_points(self, flatten=False, dtype=None, index=None):
        r"""Return the geographical coordinates in the data's original
        Coordinate Reference System (CRS).

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the coordinates to be extracted. When it is None
            all the values are extracted.

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the arrays of the x and
            y coordinates, respectively. The underlying array format
            of the field is used.

        Raises
        ------
        ValueError
            When the coordinates in the data's original CRS are not available.

        See Also
        --------
        to_latlon

        """

        def _reshape(v, flatten):
            shape = target_shape(v, flatten, self.shape)
            return array_reshape(v, shape)

        x = self.geography.x()
        y = self.geography.y()
        r = {}
        if x is not None and y is not None:
            x = _reshape(x, flatten)
            y = _reshape(y, flatten)
            if index is not None:
                x = x[index]
                y = y[index]
            r = dict(x=x, y=y)
        elif self.geography.projection().CARTOPY_CRS == "PlateCarree":
            lon, lat = self.data(("lon", "lat"), flatten=flatten, dtype=dtype, index=index)
            return dict(x=lon, y=lat)
        else:
            raise ValueError("to_points(): geographical coordinates in original CRS are not available")

        # convert values to array format
        assert r
        # sample = self._parts[DATA].get_values(dtype=dtype)
        # for k, v in zip(r.keys(), convert_array(list(r.values()), target_array_sample=sample)):
        #     r[k] = v
        # return r

        sample = self._parts[DATA].get_values(dtype=dtype)
        target_xp = eku_array_namespace(sample)
        device = target_xp.device(sample)
        target_dtype = None
        if dtype is not None:
            target_dtype = convert_dtype(dtype, target_xp)

        for k, v in r.items():
            r[k] = convert_array(v, array_namespace=target_xp, device=device)
            if target_dtype is not None:
                r[k] = target_xp.astype(r[k], target_dtype, copy=False)
        return r

    # def bounding_box(self):
    #     r"""Return the bounding box of the field.

    #     Returns
    #     -------
    #     :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
    #     """
    #     return self.geography.bounding_box

    def datetime(self):
        r"""Return the date and time of the field.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        time = self._parts[TIME].part
        return {"base_time": time.base_datetime(), "valid_time": time.valid_datetime()}

    def sel(self, *args, **kwargs):
        pass

    def isel(self, *args, **kwargs):
        pass

    def order_by(self, *args, **kwargs):
        pass

    def _unary_op(self, oper):
        v = oper(self.values)
        r = self._set_values(v)
        return r

    def _binary_op(self, oper, y):
        from earthkit.data.indexing.fieldlist import FieldList
        from earthkit.data.wrappers import get_wrapper

        y = get_wrapper(y)
        if isinstance(y, FieldList):
            x = FieldList.from_fields([self])
            return x._binary_op(oper, y)

        vx = self.values
        vy = y.values
        v = oper(vx, vy)
        r = self.set(values=v)
        return r

    def __getstate__(self):
        state = {}
        state["parts"] = self._parts
        state["private"] = self._private
        return state

    def __setstate__(self, state):

        parts = state.get("parts", {})

        self.__init__(**parts)

        private = state.get("private", {})
        self._private = private
