# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.utils.array import array_namespace as eku_array_namespace
from earthkit.utils.array import convert as convert_array
from earthkit.utils.array.convert import convert_dtype
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.core import Base
from earthkit.data.core.order import Patch, Remapping, build_remapping
from earthkit.data.decorators import normalise
from earthkit.data.utils.args import metadata_argument_new
from earthkit.data.utils.array import flatten_array, outer_indexing, reshape_array, target_shape
from earthkit.data.utils.compute import wrap_maths

_GRIB = "grib"

_LS_KEYS = [
    "parameter.variable",
    "time.valid_datetime",
    "time.base_datetime",
    "time.step",
    "vertical.level",
    "vertical.level_type",
    "ensemble.member",
    "geography.grid_type",
]


# Define field component names
_DATA = "data"
_TIME = "time"
_PARAMETER = "parameter"
_GEOGRAPHY = "geography"
_VERTICAL = "vertical"
_ENSEMBLE = "ensemble"
_PROC = "proc"
_LABELS = "labels"
_METADATA = "metadata"

_DESCRIBE_ORDER = [
    _DATA,
    _PARAMETER,
    _TIME,
    _VERTICAL,
    _ENSEMBLE,
    _GEOGRAPHY,
    _PROC,
    _LABELS,
]

_DEFAULT_DESCRIBE_SELECTION = _PARAMETER


class _ComponentMaker:
    """A factory class to delay the import of component classes."""

    def from_dict(self, name, *args, **kwargs):
        return self.default_cls(name).from_dict(*args, **kwargs)

    def from_any(self, name, *args, **kwargs):
        return self.default_cls(name).from_any(*args, **kwargs)

    def default_cls(self, name):
        return self._default_cls.get(name)

    @thread_safe_cached_property
    def _default_cls(self):
        from earthkit.data.field.handler.data import DataFieldComponentHandler
        from earthkit.data.field.handler.ensemble import EnsembleFieldComponentHandler
        from earthkit.data.field.handler.geography import GeographyFieldComponentHandler
        from earthkit.data.field.handler.labels import SimpleLabels
        from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler
        from earthkit.data.field.handler.proc import ProcFieldComponentHandler
        from earthkit.data.field.handler.time import TimeFieldComponentHandler
        from earthkit.data.field.handler.vertical import VerticalFieldComponentHandler

        return {
            _DATA: DataFieldComponentHandler,
            _TIME: TimeFieldComponentHandler,
            _PARAMETER: ParameterFieldComponentHandler,
            _GEOGRAPHY: GeographyFieldComponentHandler,
            _VERTICAL: VerticalFieldComponentHandler,
            _ENSEMBLE: EnsembleFieldComponentHandler,
            _PROC: ProcFieldComponentHandler,
            _LABELS: SimpleLabels,
        }

    def empty_object(self, name):
        cls = self.default_cls(name)
        if cls is None:
            raise ValueError(f"Unknown component name: {name}")

        if name == _LABELS:
            return cls()
        return cls.create_empty()


_COMPONENT_MAKER = _ComponentMaker()


@wrap_maths
class Field(Base):
    """A class to represent a field in Earthkit.

    A Field is a horizontal slice of the atmosphere/hydrosphere at a given time.

    A Field object is composed of several components:

    - data: the data values of the field
    - time: the temporal structure of the field (see
      :py:class:`~earthkit.data.field.component.time.TimeBase`)
    - parameter: the parameter of the field (see:
      :py:class:`~earthkit.data.field.component.parameter.ParameterBase`)
    - geography: the geography of the field (see:
      :py:class:`~earthkit.data.field.component.geography.GeographyBase`)
    - vertical: the vertical structure of the field (see:
      :py:class:`~earthkit.data.field.component.vertical.VerticalBase`)
    - ensemble: the ensemble component of the field (see:
      :py:class:`~earthkit.data.field.component.ensemble.EnsembleBase`)
    - proc: the processing component of the field (see:
      :py:class:`~earthkit.data.field.component.proc.ProcBase`)
    - labels: the labels of the field (see:
      :py:class:`~earthkit.data.field.handler.labels.SimpleLabels`)

    Field is not polymorphic, but its components are. The components are meant to be format
    independent, but they can have format specific implementations with the same interface.
    For example, the geography component of a GRIB field can have a different implementation
    than the geography component of a NetCDF field.

    Creating Fields
    ----------------
    To create a new Field object use the factory methods: :meth:`from_dict`, :meth:`from_field`
    or :meth:`from_components`.

    Values
    ----------------

    Metadata
    ---------------
    The metadata of a field can be divided into three categories:

    - Core component metadata: the metadata that is stored in the components of the field.
      Each component can be accessed by the corresponding property of the field, such as :obj:`time` for
      the time component. The metadata of a component can be accessed by the methods of the component, e.g.

      >>> field.time.valid_datetime()

      The same metadata can also be accessed by the :meth:`get` method of the field with
      the appropriate key, e.g.

      >>> field.get("time.valid_datetime")  # equivalent to field.time.valid_datetime()

    - Labels: the "labels" component of the field is a dictionary-like object that can store any
      user defined key-value pairs. It can be accessed by the :obj:`labels` property of
      the field, e.g.

      >>> field.labels # returns the labels component of the field
      >>> field.labels["my_key"] # returns the value of label "my_key"
      >>> field.labels.get("my_key")  # equivalent to field.labels["my_key"]
      >>> field.get("labels.my_key")  # equivalent to field.labels["my_key"]

    - Raw metadata: the field can also store raw metadata that is not part of any component
      or labels. For example if the field is created from a GRIB message the raw metadata
      can include all the ecCodes GRIB keys. To access the raw metadata use the :meth:`get`
      method by prefixing the raw metadata key with "metadata.", e.g.

      >>> field.get("metadata.shortName")

      The same can also be accessed by the :obj:`metadata` method of the field, which is
      can only access the raw metadata of the field, e.g.

      >>> field.metadata("shortName")
      >>> field.metadata("metadata.shortName")

      Please not that while :meth:`get` has a ``default`` argument to specify a default value when
      the key is not found, the :meth:`metadata` method does not have this argument and will raise
      a KeyError if the key is not found in the raw metadata.

      Currently it is not possible to inspect what raw metadata keys are available in a field,
      but this feature might be added in the future.


    Modifying Fields
    -----------------




    Field arithmetic
    ----------------
    The Field class supports arithmetic operations such as addition, subtraction, multiplication


    """

    _COMPONENT_NAMES = (
        _DATA,
        _TIME,
        _PARAMETER,
        _GEOGRAPHY,
        _VERTICAL,
        _ENSEMBLE,
        _PROC,
        _LABELS,
    )

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
        """
        Create a Field object.

        Do not use this constructor directly, but use the factory methods such as :meth:`from_dict`

        Parameters
        ----------
        data : DataFieldComponent
            The data of the field.
        time : TimeFieldComponent
            The temporal structure of the field.
        parameter : ParameterFieldComponent
            The parameter of the field.
        geography : GeographyFieldComponent
            The geography of the field.
        vertical : VerticalFieldComponent
            The vertical structure of the field.
        ensemble : EnsembleFieldComponentHandler
            The ensemble component of the field.
        proc : ProcFieldComponent
            The processing component of the field.
        labels : SimpleLabels
            The labels of the field.
        **kwargs : dict
            Other keyword arguments to be passed to the Field constructor.
            These can include metadata, such as `ls_keys` for GRIB fields.
        """

        def _ensure(name, value):
            if value is None:
                return _COMPONENT_MAKER.empty_object(name)
            return value

        self._components = {
            _DATA: _ensure(_DATA, data),
            _TIME: _ensure(_TIME, time),
            _PARAMETER: _ensure(_PARAMETER, parameter),
            _GEOGRAPHY: _ensure(_GEOGRAPHY, geography),
            _VERTICAL: _ensure(_VERTICAL, vertical),
            _ENSEMBLE: _ensure(_ENSEMBLE, ensemble),
            _PROC: _ensure(_PROC, proc),
            _LABELS: _ensure(_LABELS, labels),
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
        r"""Create a Field from another Field.

        Parameters
        ----------
        field : Field
            The field to copy from.
        data : DataFieldComponent, dict or None
            The new data of the field. When specified it is used instead of the data in
            the ``field``
        time : TimeBase, TimeFieldComponentHandler, dict or None
            The new time of the field. When specified it is used instead of the time
            component in the ``field``. See: :py:class:`~earthkit.data.field.component.time.TimeBase`.
        parameter : ParameterBase, ParameterFieldComponentHandler, dict or None
            The new parameter of the field. When specified it is used instead of the
            parameter component in the ``field``.
        geography : GeographyBase, GeographyFieldComponentHandler, dict or None
            The new geography of the field. When specified it is used instead of the geography
            component in the ``field``.
        vertical : VerticalBase, VerticalFieldComponentHandler, dict or None
            The new vertical level of the field. When specified it is used instead of the
            vertical component in the ``field``.
        ensemble : EnsembleBase, EnsembleFieldComponentHandler, dict or None
            The new ensemble specification of the field. When specified it is used instead of
            the ensemble component in the ``field``.
        proc : ProcBase, dict, ProcFieldComponentHandler or None
            The new processing specification of the field. When specified it is used instead of
            the processing component in the ``field``.
        labels : SimpleLabels, dict or None
            The new labels of the field. When specified it is used instead of the labels
            in the ``field``.

        Returns
        -------
        Field
            A new Field with the components copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            _DATA: data,
            _TIME: time,
            _PARAMETER: parameter,
            _GEOGRAPHY: geography,
            _VERTICAL: vertical,
            _ENSEMBLE: ensemble,
            _PROC: proc,
            _LABELS: labels,
        }

        for name in Field._COMPONENT_NAMES:
            v = _kwargs[name]
            if v is not None:
                _kwargs[name] = _COMPONENT_MAKER.default_cls(name).from_any(v)
            else:
                _kwargs[name] = field._components[name]

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
        r"""Create a Field from a dictionary.

        Parameters
        ----------
        d : dict
            The dictionary to create the Field from. Keys not used by any component
            are added to the labels.

        Returns
        -------
        Field
            A new Field created from the dictionary.
        """
        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")

        return cls.from_components(**d)

        # components = {}
        # d = d.copy()

        # # TODO: add support for proc component

        # shape_hint = None

        # if "values" in d:
        #     values = d.pop("values")
        #     components[_DATA] = cls._DEFAULT_PART_CLS[_DATA].from_dict({"values": values})
        #     shape_hint = components[_DATA].get_values(copy=False).shape

        # for name in [_TIME, _PARAMETER, _VERTICAL, _ENSEMBLE, _GEOGRAPHY]:
        #     d_component = {}
        #     for k in list(d.keys()):
        #         if k.startswith(name + "."):
        #             d_component[k.split(".", 1)[1]] = d.pop(k)

        #     # geography may need shape hint from data so handled separately
        #     if name == _GEOGRAPHY:
        #         components[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_component, shape_hint=shape_hint)
        #     else:
        #         components[name] = cls._DEFAULT_PART_CLS[name].from_dict(d_component)

        # # geography may need shape hint from data so handled separately
        # shape_hint = None
        # if components.get(_DATA):
        #     shape_hint = components[_DATA].get_values(copy=False).shape

        # # d_component = {k.split(".")[1]: v for k, v in d.items() if k.startswith(_GEOGRAPHY + ".")}
        # # components[_GEOGRAPHY] = cls._DEFAULT_PART_CLS[_GEOGRAPHY].from_dict(d, shape_hint=shape_hint)

        # # the unused items are added as labels
        # labels = SimpleLabels(d)

        # return cls(**components, labels=labels)

    @classmethod
    def from_components(
        cls,
        data=None,
        values=None,
        time=None,
        parameter=None,
        geography=None,
        vertical=None,
        ensemble=None,
        proc=None,
        labels=None,
    ):
        r"""Create a Field from components.

        Parameters
        ----------
        data : DataFieldComponent, dict
            The data of the field.
        time : Time, TimeFieldComponent, dict
            The time of the field.
        parameter : Parameter, ParameterFieldComponent, dict
            parameter component in the ``field``.
        geography : Geography, GeographyFieldComponent, dict or None
            The geography of the field.
        vertical : Vertical, VerticalFieldComponent, dict or None
            The vertical level of the field.
        ensemble : Ensemble, EnsembleFieldComponent, dict or None
            The ensemble specification of the field.
        proc :  Proc, ProcFieldComponent, dict or None
            The processing specification of the field.
        labels : SimpleLabels, dict or None
            The labels of the field.

        Returns
        -------
        Field
            A new Field with the components copied from the original field
            or specified in the keyword arguments.
        """
        _kwargs = {
            _TIME: time,
            _PARAMETER: parameter,
            _VERTICAL: vertical,
            _ENSEMBLE: ensemble,
            _PROC: proc,
            _LABELS: labels,
        }

        components = {}

        shape_hint = None
        if values is not None:
            components[_DATA] = _COMPONENT_MAKER.default_cls(_DATA).from_dict({"values": values})
            shape_hint = components[_DATA].get_values(copy=False).shape
        elif data is not None:
            components[_DATA] = _COMPONENT_MAKER.default_cls(_DATA).from_any(data)
            shape_hint = components[_DATA].get_values(copy=False).shape

        for name, v in _kwargs.items():
            if v is not None:
                component = _COMPONENT_MAKER.default_cls(name).from_any(v)
                components[name] = component

        if isinstance(geography, dict):
            components[_GEOGRAPHY] = _COMPONENT_MAKER.default_cls(_GEOGRAPHY).from_dict(
                geography, shape_hint=shape_hint
            )
        elif geography is not None:
            components[_GEOGRAPHY] = _COMPONENT_MAKER.default_cls(_GEOGRAPHY).from_any(geography)
        return cls(**components)

    @property
    def ensemble(self):
        """Ensemble: Return the ensemble component of the field."""
        return self._components[_ENSEMBLE].component

    @property
    def time(self):
        """Return the time component of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.component.time.TimeBase`
            The time component of the field.
        """
        return self._components[_TIME].component

    @property
    def vertical(self):
        """Return the vertical component of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.component.vertical.VerticalBase`
            The vertical component of the field.
        """
        return self._components[_VERTICAL].component

    @property
    def parameter(self):
        """Return the parameter component of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.component.parameter.ParameterBase`
            The parameter component of the field.
        """
        return self._components[_PARAMETER].component

    @property
    def geography(self):
        """Return the geography component of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.component.geography.GeographyBase`
            The geography component of the field.
        """
        return self._components[_GEOGRAPHY].component

    @property
    def proc(self):
        """Return the proc component of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.component.proc.ProcBase`
            The proc component of the field.
        """
        return self._components[_PROC].component

    @property
    def labels(self):
        """Return the labels of the field.

        Returns
        -------
        :py:class:`~earthkit.data.field.handler.labels.SimpleLabels`
            The labels of the field.
        """
        return self._components[_LABELS]

    @property
    def array_namespace(self):
        r""":obj:`ArrayNamespace`: Return the array namespace of the field."""
        return eku_array_namespace(self.values)

    # def free(self):
    #     self._components[_DATA] = self._components[_DATA].Offloader(self._components[_DATA])

    @property
    def values(self):
        """Return the values of the fields as a flat array.

        Returns
        -------
        array-like
            Flat array containing the field values without performing any copying or conversion. The underlying
            array format of the field is used. For GRIB it is a numpy array.

        See Also
        --------
        to_numpy
        to_array

        Examples
        --------
        >>> import earthkit.data as ekd
        >>> f = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
        >>> v = f.values
        >>> v.shape
        (209,)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        return self._components[_DATA].values

    @property
    def shape(self):
        """tuple: Return the shape of the field."""
        try:
            v = self.geography.shape()
        except Exception:
            v = None

        return v if v is not None else self.values.shape

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
        copy: bool
            When it is True a copy of the data is returned. Otherwise a view is returned where possible.
        index: ndarray indexing object, optional
            The index of the values to be extracted. When it
            is None all the values are extracted

        Returns
        -------
        ndarray
            Field values

        """
        v = self._components[_DATA].get_values(dtype=dtype, copy=copy)
        v = convert_array(v, array_namespace="numpy")
        v = flatten_array(v) if flatten else reshape_array(v, self.shape)

        if index is not None:
            v = outer_indexing(v, index)

        return v

    def to_array(
        self,
        flatten=False,
        dtype=None,
        copy=True,
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
        copy: bool
            When it is True a copy of the data is returned. Otherwise a view is returned where possible.
        array_namespace: str, array_namespace or None
            The array namespace to be used. When it is :obj:`None` the underlying array format
            of the field is used. **New in version 0.19.0**.
        device: str or None
            The device where the array will be allocated. When it is :obj:`None` the default device is used.
        index: array indexing object, optional
            The index of the values to be extracted. When it
            is None all the values are extracted.

        Returns
        -------
        array-array
            Field values.

        """
        v = self._components[_DATA].get_values(dtype=dtype, copy=copy)
        if array_namespace is not None:
            v = convert_array(v, array_namespace=array_namespace, device=device)

        v = flatten_array(v) if flatten else reshape_array(v, self.shape)
        if index is not None:
            v = outer_indexing(v, index)

        return v

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

        See Also
        --------
        geography
        to_numpy
        value

        Examples
        --------
        How-to examples for the :meth:`data` method can be found in the following notebooks:

        - :ref:`/how-tos/grib/grib_lat_lon_value_ll.ipynb`
        - :ref:`/how-tos/grib/grib_lat_lon_value_rgg.ipynb`

        Other examples:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("file", "docs/how-tos/test6.grib").to_fieldlist()
        >>> d = fl[0].data()
        >>> d.shape
        (3, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2, 0, 0]  # first value
        272.56417847
        >>> d = fl[0].data(keys="lon")
        >>> d.shape
        (7, 12)
        >>> d[0, 0]  # first longitude
        0.0

        """
        _keys = dict(
            lat=self.geography.latitudes,
            lon=self.geography.longitudes,
            value=self.to_numpy,
        )

        if isinstance(keys, str):
            keys = [keys]

        for k in keys:
            if k not in _keys:
                raise ValueError(f"data: invalid argument: {k}")

        def _reshape(v, flatten):
            shape = target_shape(v, flatten, self.shape)
            return reshape_array(v, shape)

        r = {}
        for k in keys:
            # TODO: convert dtype
            v = _keys[k](dtype=dtype)
            # v = _keys[k]
            if v is None:
                raise ValueError(f"data: {k} not available")
            v = _reshape(v, flatten)
            if index is not None:
                v = outer_indexing(v, index)
            r[k] = v

        # convert latlon to array format
        ll = {k: r[k] for k in r if k != "value"}
        if ll:
            sample = r.get("value", None)
            if sample is None:
                sample = self._components[_DATA].get_values(dtype=dtype)
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

    def _get_component(self, key):
        if "." in key:
            component_name, name = key.split(".", 1)
            return component_name, self._components.get(component_name), name
        elif key in self._components[_DATA]:
            return _DATA, self._components[_DATA], key
        return None, None, key

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        r"""Return the value for the key.

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
        component_name, component, key_name = self._get_component(key)

        if component:
            return component.get(key_name, default=default, astype=astype, raise_on_missing=raise_on_missing)
        elif component_name == _METADATA:
            for _, private_component in self._private.items():
                if hasattr(private_component, "metadata"):
                    return private_component.metadata(
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
                    v = self.private_component.get(key)
                    if v is not None:
                        return _cast(v)

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in field")

        return default

    def _get_single_collection(self, key, raise_on_missing=False):
        component_name = key
        component = self._components.get(key)

        if component:
            return component.component.to_dict()
        else:
            prefix, _, sub_name = component_name.rpartition(".")
            if prefix == _METADATA:
                for _, private_component in self._private.items():
                    if hasattr(private_component, "as_namespace"):
                        return private_component.as_namespace(sub_name)

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in field")

    def _get_fast(
        self,
        keys=None,
        collections=None,
        default=None,
        astype=None,
        raise_on_missing=False,
        output=None,
        flatten_dict=False,
        remapping=None,
    ):
        r"""Fast(er) implementation of :meth:`get` for internal use. This method assumes that the
        arguments have been normalised e.g. by using :func:`metadata_argument_new`. No checks
        are performed on the arguments to ensure that they are valid and consistent.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None, or a list/tuple thereof
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. Must have the same "structure" as ``keys``.
        astype: type as str, int or float, or a list/tuple thereof
            Return type for ``keys``. Must have the same "structure" as ``keys``.
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
        This method assumes that the arguments have been normalised e.g. by using
        :func:`metadata_argument_new`. No checks are performed on the arguments to
        ensure that they are valid and consistent.
        """
        meth = self._get_single
        # Remapping must be an object if defined
        if remapping is not None:
            assert isinstance(remapping, (Remapping, Patch))
            meth = remapping(meth)

        result = None
        multi = keys and collections

        if isinstance(keys, str):
            result = meth(keys, default=default, astype=astype, raise_on_missing=raise_on_missing)
            if output is dict:
                result = {keys: result}
            elif multi:
                result = [keys]
        elif isinstance(keys, (list, tuple)):
            if output is not dict:
                result = [
                    meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                ]
            #     if output is tuple:
            #         result = tuple(result)
            else:
                result = {
                    k: meth(k, astype=kt, default=d, raise_on_missing=raise_on_missing)
                    for k, kt, d in zip(keys, astype, default)
                }

        if collections:
            if isinstance(collections, str):
                r = self._get_single_collection(collections, raise_on_missing=raise_on_missing)
                if output is dict:
                    if result is not None:
                        result[collections] = r
                    else:
                        result = {collections: r}
                elif result is not None:
                    result.append(r)
                else:
                    result = r
            elif isinstance(collections, (list, tuple)):
                if output is not dict:
                    r = [self._get_single_collection(k, raise_on_missing=raise_on_missing) for k in collections]
                    # if output is tuple:
                    #     result = tuple(result)
                    if result is not None:
                        result.extend(r)
                    else:
                        result = r
                else:
                    r = {k: self._get_single_collection(k, raise_on_missing=raise_on_missing) for k in collections}
                    if result is not None:
                        result.update(r)
                    else:
                        result = r

        if output is dict and flatten_dict:
            r = {}
            for k, v in result.items():
                if isinstance(v, dict):
                    for _k, _v in v.items():
                        r[k + "." + _k] = _v
                else:
                    r[k] = v
            result = r

        if output is tuple:
            result = tuple(result)

        return result

    def get(
        self,
        keys=None,
        default=None,
        *,
        astype=None,
        raise_on_missing=False,
        collections=None,
        output="auto",
        flatten_dict=False,
        remapping=None,
        patch=None,
    ):
        r"""Return the values for the specified keys.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the field metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str. Keys are assumed to be of the form
            "component.key". For example, "time.valid_datetime" or "parameter.name". Keys from the
            raw metadata (if any) can be accessed using the "metadata.key" syntax.
            For example, when a :obj:`Field` was created from a GRIB message, the ecCodes GRIB keys can
            be accessed as "metadata.shortName" or "metadata.level".
        default: Any, None
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. When ``default`` is a single
            value, it is used for all the keys. Otherwise it must be a list/tuple of the
            same length as ``keys``.
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
            It is only applied to keys returning a single value.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.
        collections: str, list or tuple
            Specify the metadata collections to extract. Can be a single collection (str) or multiple
            collections as a list/tuple of str. A collection is a component of the field (e.g. "time",
            "parameter", "geography", etc.) as a dictionary. It can also be a collection within the
            raw "metadata" component. For example, when a :obj:`Field` was created from a GRIB
            message, the ecCodes GRIB "namespaces" can be accessed as collections, e.g. "metadata.mars"
            means the ecCodes GRIB "mars" namespace. The returned value for a collection is a dictionary with
            the keys and values in the collection. To flatten the returned dictionary for a collection, use
            the ``output==dict`` and ``flatten_dict=True`` options.
        output: type, str
            Specify the output type. Can be:

            - "auto" (default):
                - when ``keys`` is a str returns a single value
                - when ``keys`` is a list/tuple returns a list/tuple of values
            - list or "list": returns a list of values.
            - tuple or "tuple": returns a tuple of values.
            - dict or "dict": returns a dictionary with keys and their values.

            Other types are not supported.
        flatten_dict: bool
            When True and ``output`` is dict, if any of the values in the returned dict
            is itself a dict, it is flattened to depth 1 by concatenating the keys with a dot. For example, if the
            returned dict is ``{"a": {"x": 1, "y": 2}, "b": 3}``, it becomes ``{"a.x": 1, "a.y": 2, "b": 3}``.
            This option is ignored when ``output`` is not dict.
        remapping: dict, optional
            Create new metadata keys from existing ones. E.g. to define a new
            key "param_level" as the concatenated value of the "parameter.variable" and "vertical.level" keys use::

                remapping={"param_level": "{parameter.variable}{vertical.level}"}

        patch: dict, optional
            A dictionary of patch to be applied to the returned values.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``. The structure of the returned value(s) depends on the ``output``
            and ``flatten_dict`` parameters.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.


        Examples
        --------
        >>> import earthkit.data as ekd
        >>> f = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
        >>> f.get("parameter.variable")
        '2t'

        Get multiple keys as a list/tuple of values:

        >>> f.get(["parameter.variable", "parameter.units"])
        ['2t', 'K']
        >>> f.get(("parameter.variable", "parameter.units"))
        ('2t', 'K')

        Get multiple keys as a dictionary:

        >>> f.get(["parameter.variable", "parameter.units"], output="dict")
        {'parameter.variable': '2t', 'parameter.units': 'K'}

        Get collections:

        >>> f.get(collections="time")
        {'base_datetime': datetime.datetime(2020, 5, 13, 0, 0),
        'step': datetime.timedelta(hours=0),
        'valid_datetime': datetime.datetime(2020, 5, 13, 0, 0)}
        >>> f.get(collections=["time", "parameter"])
        [{'base_datetime': datetime.datetime(2020, 5, 13, 0, 0),
        'step': datetime.timedelta(hours=0 ),
        'valid_datetime': datetime.datetime(2020, 5, 13, 0, 0)},
        {'variable': '2t',
        'units': 'K'}]
        >>> f.get(collections=["time", "parameter"], dict=True)
        {'time': {'base_datetime': datetime.datetime(2020, 5, 13, 0, 0),
        'step': datetime.timedelta(hours=0 ),
        'valid_datetime': datetime.datetime(2020, 5, 13, 0, 0)},
        'parameter': {'variable': '2t',
        'units': 'K'}}

        Use ``output=dict`` and ``flatten_dict=True`` to flatten the returned dictionary for collections:

        >>> f.get(collections=["time"], output="dict", flatten_dict=True)
        {'time.base_datetime': datetime.datetime(2020, 5, 13, 0, 0),
        'time.step': datetime.timedelta(hours=0),
        'time.valid_datetime': datetime.datetime(2020, 5, 13, 0, 0)}

        Get the ecCodes GRIB "mars" namespace as a collection from the raw metadata
        (result trimmed for brevity):
        >>> f.get(collections="metadata.mars", output="dict")
        {"metadata.mars": {'class': 'od', 'date': 20200513, 'expver': '0001'}}

        Mix keys and collections (result trimmed for brevity):

        >>> f.get(keys="metadata.shortName", collections="metadata.mars", output="dict")
        {'metadata.shortName': '2t', 'metadata.mars': {'class': 'od', 'date': 20200513, 'expver': '0001'}}
        >>> f.get(keys="metadata.shortName", collections="metadata.mars", output="dict", flatten_dict=True)
        {'metadata.shortName': '2t',
        'metadata.mars.class': 'od',
        'metadata.mars.date': 20200513,
        'metadata.mars.expver': '0001'}

        """
        if not keys and not collections:
            raise ValueError("At least one key or collection must be specified.")

        keys, astype, default, keys_arg_type = metadata_argument_new(
            keys,
            default=default,
            astype=astype,
        )

        if output == "auto":
            if keys_arg_type is not str:
                output = keys_arg_type
        elif output in [list, "list"]:
            output = list
        elif output in [tuple, "tuple"]:
            output = tuple
        elif output in [dict, "dict"]:
            output = dict
        else:
            raise ValueError(f"Invalid output: {output}")

        if remapping or patch:
            remapping = build_remapping(remapping, patch, forced_build=False)

        return self._get_fast(
            keys,
            collections,
            default=default,
            astype=astype,
            raise_on_missing=raise_on_missing,
            remapping=remapping,
            output=output,
            flatten_dict=flatten_dict,
        )

    def metadata(
        self,
        keys,
        *,
        astype=None,
        output="auto",
        remapping=None,
        patch=None,
    ):
        r"""Return the raw metadata values.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the raw metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str. Keys can be optionally prefixed with "metadata.". For example,
            if the raw metadata has the key "shortName", it can also be specified
            as "metadata.shortName".
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
            It is only applied to keys returning a single value.
        output: type, str
            Specify the output type. Can be:

            - "auto" (default):
                - when ``keys`` is a str returns a single value
                - when ``keys`` is a list/tuple returns a list/tuple of values
            - list or "list": returns a list of values.
            - tuple or "tuple": returns a tuple of values.
            - dict or "dict": returns a dictionary with keys and their values.
            Other types are not supported.
        remapping: dict, optional
            Create new metadata keys from existing ones. E.g. to define a new
            key "param_level" as the concatenated value of the "param" and "level" keys use::

                remapping={"param_level": "{param}{level}"}

        patch: dict, optional
            A dictionary of patch to be applied to the returned values.

        Returns
        -------
        single value, list, tuple or dict
            The values for the specified ``keys``. The structure of the returned value(s) depends on the ``output``
            and ``flatten_dict`` parameters.

        Raises
        ------
        KeyError
            If any of ``keys`` is not found in the raw metadata.


        Examples
        --------
        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
        >>> f = fl[0]
        >>> f.metadata("shortName")
        '2t'
        >>> f.metadata(["shortName", "units"])
        ['2t', 'K']
        >>> f.metadata(("shortName", "units"))
        ('2t', 'K')

        """
        if isinstance(keys, str) and not keys.startswith("metadata."):
            keys = "metadata." + keys
        else:
            is_tuple = isinstance(keys, tuple)
            keys = ["metadata." + x for x in keys if not x.startswith("metadata.")]
            if is_tuple:
                keys = tuple(keys)

        return self.get(
            keys,
            astype=astype,
            raise_on_missing=True,
            output=output,
            remapping=remapping,
            patch=patch,
        )

    def set(self, *args, **kwargs):
        """Return a new field with the specified metadata keys set to the given values.

        Parameters
        ----------
        *args: tuple
            Positional arguments used to specify the metadata keys and values to set. Each
            argument can be a dict with keys and values to set. When multiple dicts are given
            they are merged together with the latter dicts taking precedence over the former
            ones.

            >>> field.set({"parameter.variable": "t"})
            >>> field.set({"parameter.variable": "t", "vertical.level": 1000})

            New data values can  be set by using the "data" or "values" key with the new values
            as a value. For example,

            >>> field.set(data=new_values_array)

            will replace the data values in the field with the values in ``new_values_array``.

            Only high-level metadata keys (and "data" or "values") are allowed here, i.e. keys that
            belong to a component. Modifying raw metadata keys is not allowed and we cannot use them
            in :meth:`set` with or without the "metadata." prefix. For example, although
            in fields generated from GRIB we can use the "metadata.shortName" key in the :meth:`get`
            method to access the "shortName" key we cannot use it in :meth:`set`.

            Entire components can be set by using the component name as a key and the component
            object or the equivalent dict as a value. For example,

            >>> field.set(parameter={"variable": "t", "units": "K"})

            will replace the entire parameter component.

            Date and time related keys from the "time" field component can take
            different formats of date/time/duration values as input. For example, when
            setting by "time.base_datetime" the following calls are equivalent:

            >>> fl.set({ "time.base_datetime": "2018-08-01T12"})
            >>> fl.set({ "time.base_datetime": datetime(2018, 8, 1, 12, 0) })

            Similarly, when setting "time.step" the following calls are equivalent.

            >>> fl.set({ "time.step": "6h"})
            >>> fl.set({ "time.step": 6})
            >>> fl.set({ "time.step": "360m"})
            >>> fl.set({ "time.step": timedelta(hours=6)})

            Values are assumed to be in hours when the unit is not specified. When the unit is specified
            it can be either "h", "m" or "s" for hours, minutes or seconds, respectively.

        **kwargs: dict
            Keyword arguments used to specify the metadata keys and values to set. They take
            precedence over the positional arguments. The same rules for the keys and values
            as for the positional arguments apply here.

        Returns
        -------
        Field
            A new field with the specified metadata keys set to the given values.

        Examples
        --------
        See the how-to examples for the :meth:`set` method in the following notebook:

        - :ref:`/how-tos/grib/grib_modify_metadata.ipynb`
        - :ref:`/how-tos/grib/grib_modify_values.ipynb`

        Further examples:

        >>> import earthkit.data as ekd
        >>> fl = ekd.from_source("sample", "test.grib").to_fieldlist()
        >>> f = fl[0]
        >>> f2 = f.set({"parameter.variable": "10t", "parameter.units": "K"})
        >>> f2.get(["parameter.variable", "parameter.units"])
        ['10t', 'K']

        """
        kwargs = kwargs.copy()
        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                kwargs.update(a)
                continue
            raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

        _kwargs = defaultdict(dict)

        if not kwargs:
            return self

        _components = dict()
        for k, v in kwargs.items():
            if k in self._components:
                _components[k] = v
            else:
                component_name, component, key_name = self._get_component(k)
                if component is not None:
                    if key_name is not None and key_name != "":
                        _kwargs[component_name][key_name] = v
                    else:
                        raise KeyError(f"Key {k} cannot be set on the field.")
                else:
                    raise KeyError(f"Key {k} cannot be set on the field.")

        for k in _components:
            if k in _kwargs:
                raise KeyError(
                    f"Keys {_kwargs.keys()} cannot be set on the field because component={k} is also specified."
                )

        if _kwargs:
            for component_name, v in _kwargs.items():
                component = self._components[component_name]
                s = component.set(**v)
                _components[component_name] = s

        if _components:
            return Field.from_field(self, **_components)
        elif kwargs:
            raise ValueError("No valid keys to set in the field.")

        return None

    def _set_values(self, array):
        data = self._components[_DATA].set_values(array)
        return Field.from_field(self, data=data)

    def to_target(self, target, *args, **kwargs):
        r"""Write the field into a target object.

        Parameters
        ----------
        target: object
            The :ref:`target <data-target-objects>` to write the field into.
        *args: tuple
            Positional arguments used to specify the target object.
        **kwargs: dict, optional
            Other keyword arguments used to write the field into the target object.

        See Also
        --------
        :ref:`targets`
        :ref:`data-target-objects`

        Examples
        --------
        How-to examples for the :meth:`to_target` method can be found in the following notebooks:

        - :ref:`/how-tos/target/file_target.ipynb`
        - :ref:`/how-tos/target/grib_to_file_target.ipynb`
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def _default_encoder(self):
        val = self._private.get("default_encoder") if self._private else None
        if val is not None:
            return val
        if self._get_grib():
            return "grib"
        else:
            return None

    def _encode(self, encoder, hints=None, **kwargs):
        """Double dispatch to the encoder."""
        return encoder._encode_field(self, **kwargs)

    def to_field(self, array=True):
        """Return the field itself."""
        return self

    # TODO: review this method since it is GRIB specific and may not be applicable to other formats
    def to_array_field(self, array_namespace=None, device=None, flatten=False, dtype=None):
        grib = self._get_grib()
        if grib is not None:
            return grib.new_array_field(
                self, array_namespace=array_namespace, device=device, flatten=flatten, dtype=dtype
            )
        return self

    # TODO: review this method. Not clear if it needs arguments. Consider a static method instead.
    def to_fieldlist(self, fields=None):
        from earthkit.data.indexing.simple import SimpleFieldList

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
        return self._dispatch_to_fieldlist_method("to_xarray", *args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert the Field into a Pandas DataFrame.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`FieldList.to_pandas`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`FieldList.to_pandas`.

        Returns
        -------
        Pandas DataFrame

        """
        return self._dispatch_to_fieldlist_method("to_pandas", *args, **kwargs)

    def _dump_component(self, component="all", *, filter=None, prefix_keys=False, unwrap_single=True):
        r"""Return the components as a dict.

        Parameters
        ----------
        component: :obj:`str`, :obj:`list`, :obj:`tuple` or :obj:`all`
            The component to return. If `component` is :obj:`all`, None or empty str
            all the components will be used.

        Returns
        -------
        dict
            Each namespace is represented as a dict. When ``simplify`` is True and
            ``component`` is a str and only one namespace is available the returned dict
            contains the keys and values of that namespace. Otherwise the returned
            dict contains one item per namespace.


        See Also
        --------
        dump


        Examples
        --------
        :ref:`/how-tos/grib/grib_contents.ipynb`

        """
        if component is None or component == "":
            raise ValueError("_dump_component(): component cannot be None or empty str. Use 'all' instead.")

        if component in ["all", all, ["all"], [all]]:
            component = None

        result = {}
        for m in self._components.values():
            m.dump(self, component, result, prefix_keys=prefix_keys)

        if component and not isinstance(component, str):
            if "metadata" in component:
                component = "metadata"

        if component == "metadata" and self._private:
            md = self._private.get("metadata")
            if md and hasattr(md, "namespace"):
                md.namespace(self, filter, result, prefix_keys=prefix_keys)

        if unwrap_single and isinstance(component, str) and len(result) == 1 and component in result:
            return result[component]

        return result

    def describe(self, component=all, filter=None, **kwargs):
        r"""Generate dump with all the metadata keys belonging to ``namespace``.

        In a Jupyter notebook it is represented as a tabbed interface.

        Parameters
        ----------
        component: :obj:`str`, :obj:`list`, :obj:`tuple`, :obj:`None` or :obj:`all`
            The component(s) to include. The following values
            have a special meaning:

            - :obj:`all`: all the available components will be used.


        **kwargs: dict, optional
            Other keyword arguments used for testing only

        Returns
        -------
        NamespaceDump
            Dict-like object with one item s per component. In a Jupyter notebook represented
            as a tabbed interface to browse the dump con stents.


        See Also
        --------
        namespace


        Examples
        --------
        :ref:`/how-tos/grib/grib_contents.ipynb`

        """
        from earthkit.data.utils.summary import format_namespace_dump

        d = self._dump_component(component, filter=filter, unwrap_single=False)

        d1 = {}
        for k in _DESCRIBE_ORDER:
            if k in d:
                d1[k] = d.pop(k)

        d1.update(d)
        d = d1

        r = []
        for ns, v in d1.items():
            # v = self.as_namespace(ns)
            if v:
                r.append({
                    "title": ns if ns else "default",
                    "data": v,
                    "tooltip": f"Keys in the {ns} namespace",
                })

        return format_namespace_dump(r, selected=_DEFAULT_DESCRIBE_SELECTION, details=self.__class__.__name__, **kwargs)

    @property
    def default_ls_keys(self):
        """list: Return the default keys to be used for the :meth:`ls` method."""
        return _LS_KEYS

    def ls(
        self,
        n=None,
        keys="default",
        extra_keys=None,
        collections=None,
    ):
        r"""Generate a one row summary of the Field using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            This parameter is ignored since the summary is generated for a single field. It is
            only used for compatibility with the
            :py:meth:`earthkit.data.core.fieldlist.FieldList.ls` method.
        keys: list of str, dict, None
            The metadata keys to extract. If ``keys="default"``, a built-in default set of keys is used.
            To specify a column title for each key in the output use a dict as a mapping from the keys to the
            column titles.
        extra_keys: list of str, dict, None
            List of additional keys on top of ``keys``. To specify a column title for each key in the output
            use a dict as a mapping from the keys to the column titles.
        collections: str, list of str, None
            The collections to extract. Can be a single collection (str) or multiple collections as a
            list of str. A collection is a component of the field (e.g. "time", "parameter",
            "geography", etc.) as a dictionary. It can also be a collection within the raw
            "metadata" component. For example, when a :obj:`Field` was created from a GRIB message, the
            ecCodes GRIB "namespaces" can be accessed as collections, e.g. "metadata.mars" means
            the ecCodes GRIB "mars" namespace.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`Field`.

        See Also
        --------
        head
        tail

        """
        return self._dispatch_to_fieldlist_method(
            "ls", n=None, keys=keys, extra_keys=extra_keys, collections=collections
        )

    def head(self, *args, **kwargs):
        r"""Generate a one row summary of the Field using a set of metadata keys.

        Same as calling :obj:`ls`.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`ls`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See :obj:`ls`.

        See Also
        --------
        ls
        tail

        """
        return self.ls("head", *args, **kwargs)

    def tail(self, *args, **kwargs):
        r"""Generate a one row summary of the Field using a set of metadata keys.

        Same as calling :obj:`ls`.

        Parameters
        ----------
        *args: tuple
            Positional arguments passed to :obj:`ls`.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See :obj:`ls`.

        See Also
        --------
        ls
        tail

        """
        return self.ls("tail", *args, **kwargs)

    def message(self):
        r"""Return a buffer containing the encoded message for Fields generated from a message based format (e.g. GRIB).

        Returns
        -------
        bytes
        """
        grib = self._get_grib()
        if grib is not None:
            return grib.message()
        return None

    def _dispatch_to_fieldlist_method(self, method_name, *args, **kwargs):
        method = getattr(self.to_fieldlist(), method_name)
        return method(*args, **kwargs)

    def _set_private_data(self, name, data):
        self._private[name] = data

    def _get_private_data(self, name):
        return self._private.get(name)

    def _get_grib(self):
        if self._private and "metadata" in self._private and getattr(self._private["metadata"], "NAME", None) == _GRIB:
            return self._private["metadata"]

        return None

    def _check(self):
        return
        # for m in self._components.values():
        #     m.check(self)

    def _get_grib_context(self, context):
        grib = self._get_grib()
        if grib is not None:
            context["handle"] = grib.handle

        for m in self._components.values():
            m.get_grib_context(context)

    @normalise("time.valid_datetime", "date")
    @normalise("time.base_datetime", "date")
    @normalise("time.forecast_reference_time", "date")
    @normalise("time.step", "timedelta")
    @normalise("base_datetime", "date")
    @normalise("valid_datetime", "date")
    @normalise("step_timedelta", "timedelta")
    @normalise("metadata.base_datetime", "date")
    @normalise("metadata.valid_datetime", "date")
    @normalise("metadata.step_timedelta", "timedelta")
    @staticmethod
    def _normalise_key_values(**kwargs):
        r"""Normalise the selection input for :meth:`FieldList.sel`."""
        return kwargs

    # def sel(self, *args, **kwargs):
    #     r"""Check if a field matches the given selection criteria.

    #     Parameters
    #     ----------
    #     *args: tuple
    #         Positional arguments specifying the filter conditions as a dict.
    #         Both single or multiple keys are allowed to use. When multiple filter conditions
    #         are specified, they are combined with a logical AND operator. Each metadata key in
    #         the filter conditions can specify the following type of filter values:

    #         - single value::

    #             f.sel({parameter.variable: "t"})

    #         - list of values::

    #             f.sel({parameter.variable: ["u", "v"]})

    #         - slice of values (defines a closed interval, so treated as inclusive of both the start
    #         and stop values, unlike normal Python indexing). The following example filters the fields
    #         with "vertical.level" between 300 and 500 inclusively::

    #             f.sel({vertical.level: slice(300, 500)})

    #         Date and time related keys from the "time" field component are automatically normalised
    #         for comparison. This is also applied to the following keys from the
    #         raw metadata: "metadata.base_datetime", "metadata.valid_datetime" and "metadata.step_timedelta".

    #         For example, when filtering by "time.valid_datetime" the following calls are equivalent:

    #         >>> f.sel({ "time.valid_datetime": "2018-08-01T12:00:00"})
    #         >>> f.sel({ "time.valid_datetime": "2018080112"})
    #         >>> f.sel({ "time.valid_datetime": 2018080112})
    #         >>> f.sel({ "time.valid_datetime": datetime(2018, 8, 1, 12, 0) })

    #         Similarly, when filtering by "time.step" the following calls are equivalent (values are assumed
    #         to be in hours when the unit is not specified):

    #         >>> f.sel({ "time.step": "6h"})
    #         >>> f.sel({ "time.step": 6})
    #         >>> f.sel({ "time.step": "360m"})
    #         >>> f.sel({ "time.step": timedelta(hours=6)})

    #     remapping: dict
    #         Define new metadata keys from existing ones to use in ``*args`` and ``**kwargs``.
    #         E.g. to define a new key "param_level" as the concatenated value of
    #         the "parameter.variable" and "vertical.level" keys use::

    #         >>> remapping={"param_level": "{parameter.variable}{vertical.level}"}

    #     **kwargs: dict, optional
    #         Other keyword arguments specifying the filter conditions.

    #     Returns
    #     -------
    #     Field or None
    #         Returns the field itself if it matches the selection criteria, otherwise returns None.
    #     """
    #     res = self._dispatch_to_fieldlist_method("sel", *args, **kwargs)

    #     if res and len(res) == 1:
    #         return self
    #     return None

    # def order_by(self, *args, **kwargs):
    #     pass

    def _unary_op(self, oper):
        v = oper(self.values)
        r = self._set_values(v)
        return r

    def _binary_op(self, oper, y):
        from earthkit.data.core.fieldlist import FieldList
        from earthkit.data.data.wrappers import from_object
        from earthkit.data.indexing.indexed import IndexFieldListBase

        y = from_object(y)
        if isinstance(y, FieldList):
            x = IndexFieldListBase.from_fields([self])
            return x._binary_op(oper, y)

        vx = self.values
        vy = y.to_numpy(flatten=True)
        v = oper(vx, vy)
        r = self.set(values=v)
        return r

    def __repr__(self):
        r = []
        for k in _LS_KEYS:
            r.append(f"{self.get(k, default=None)}")
        return f"Field({', '.join(r)})"

    def _repr_html_(self):
        return self.describe()._repr_html_()

    def __getstate__(self):
        state = {}
        state["components"] = self._components
        state["private"] = self._private
        return state

    def __setstate__(self, state):
        components = state.get("components", {})
        self.__init__(**components)
        private = state.get("private", {})
        self._private = private
