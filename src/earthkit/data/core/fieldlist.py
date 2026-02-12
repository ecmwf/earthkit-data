# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.core import Base


class FieldListCore(Base):
    @abstractmethod
    def __getitem__(self, index):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @staticmethod
    @abstractmethod
    def from_fields(fields):
        pass

    @staticmethod
    @abstractmethod
    def from_numpy(array, metadata):
        pass

    @staticmethod
    @abstractmethod
    def from_array(array, metadata):
        r"""Create an :class:`SimpleFieldList`.

        Parameters
        ----------
        array: array-like, list
            The fields' values. When it is a list it must contain one array per field.
        metadata: list, :class:`Metadata`
            The fields' metadata. Must contain one :class:`Metadata` object per field. Or
            it can be a single :class:`Metadata` object when all the fields have the same metadata.

        In the generated :class:`SimpleFieldList`, each field is represented by an array
        storing the field values and a :class:`MetaData` object holding
        the field metadata. The shape and dtype of the array is controlled by the ``kwargs``.
        """
        pass

    @property
    @abstractmethod
    def values(self):
        """array-like: Get all the fields' values as a 2D array. It is formed as the array of
        :obj:`GribField.values <data.readers.grib.codes.GribField.values>` per field.

        See Also
        --------
        to_array

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.values.shape)
        ...
        (209,)
        (209,)
        >>> v = ds.values
        >>> v.shape
        (2, 209)
        >>> v[0][:3]
        array([262.78027344, 267.44726562, 268.61230469])

        """
        pass

    @abstractmethod
    def to_array(self, **kwargs):
        r"""Return all the fields' values as an array. It is formed as the array of the
        :obj:`data.core.fieldlist.Field.to_array` values per field.

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to :obj:`data.core.fieldlist.Field.to_array`

        Returns
        -------
        array-like
            Array containing the field values.

        See Also
        --------
        values
        to_numpy
        """
        pass

    @abstractmethod
    def data(
        self,
        keys=("lat", "lon", "value"),
        flatten=False,
        dtype=None,
        index=None,
    ):
        r"""Return the values and/or the geographical coordinates.

        Only works when all the fields have the same grid geometry.

        Parameters
        ----------
        keys: :obj:`str`, :obj:`list` or :obj:`tuple`
            Specifies the type of data to be returned. Any combination of "lat", "lon" and "value"
            is allowed here.
        flatten: bool
            When it is True the "lat", "lon" arrays and the "value" arrays per field
            will all be flattened. Otherwise they will preserve the field's :obj:`shape`.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.
        index: array indexing object, optional
            The index of the values to be extracted from each field. When it is None all the
            values are extracted.

        Returns
        -------
        array-like
            The elements of the array (in the order of the ``keys``) are as follows:

            * the latitudes array from the first field  when "lat" is in ``keys``
            * the longitudes array from the first field when "lon" is in ``keys``
            * a values array per field when "values" is in ``keys``

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry.

        Examples
        --------
        - :ref:`/examples/grib_lat_lon_value.ipynb`

        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
        >>> len(ds)
        6
        >>> d = ds.data()
        >>> d.shape
        (8, 7, 12)
        >>> d[0, 0, 0]  # first latitude
        90.0
        >>> d[1, 0, 0]  # first longitude
        0.0
        >>> d[2:, 0, 0]  # first value per field
        array([272.56417847,  -6.28688049,   7.83348083, 272.53916931,
                -4.89837646,   8.66096497])
        >>> d = ds.data(keys="lon")
        >>> d.shape
        (1, 7, 12)
        >>> d[0, 0, 0]  # first longitude
        0.0

        See Also
        --------
        geography
        to_numpy
        values

        """
        pass

    # @abstractmethod
    # def datetime(self):
    #     r"""Return the unique, sorted list of dates and times in the fieldlist.

    #     Returns
    #     -------
    #     dict of datatime.datetime
    #         Dict with items "base_time" and "valid_time".

    #     Examples
    #     --------
    #     >>> import earthkit.data
    #     >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
    #     >>> ds.datetime()
    #     {'base_time': [datetime.datetime(2020, 12, 21, 12, 0)],
    #     'valid_time': [
    #         datetime.datetime(2020, 12, 21, 12, 0),
    #         datetime.datetime(2020, 12, 21, 15, 0),
    #         datetime.datetime(2020, 12, 21, 18, 0),
    #         datetime.datetime(2020, 12, 21, 21, 0),
    #         datetime.datetime(2020, 12, 23, 12, 0)]}

    #     """

    @property
    @abstractmethod
    def geography(self):
        pass

    # @abstractmethod
    # def projection(self):
    #     r"""Return the projection information shared by all the fields.

    #     Returns
    #     -------
    #     :obj:`Projection`

    #     Raises
    #     ------
    #     ValueError
    #         When not all the fields have the same grid geometry

    #     Examples
    #     --------
    #     >>> import earthkit.data
    #     >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
    #     >>> ds.projection()
    #     <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
    #     Name: unknown
    #     Axis Info [cartesian]:
    #     - E[east]: Easting (unknown)
    #     - N[north]: Northing (unknown)
    #     - h[up]: Ellipsoidal height (metre)
    #     Area of Use:
    #     - undefined
    #     Coordinate Operation:
    #     - name: unknown
    #     - method: Equidistant Cylindrical
    #     Datum: Unknown based on WGS 84 ellipsoid
    #     - Ellipsoid: WGS 84
    #     - Prime Meridian: Greenwich
    #     >>> ds.projection().to_proj_string()
    #     '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
    #     """
    #     pass

    @abstractmethod
    def get(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output="item_per_field",
        remapping=None,
        patches=None,
    ):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        keys: str, list, tuple
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
        output: str, default=item_per_field
            Specify the output structure. Possible values are:

            - item_per_field: returns a list with one item per field. If a single key is
                given the item is the value for that key. If a list
                of keys are given the item is a list of values for those keys. Similarly,
                when ``keys`` is a tuple each item is a tuple of values.
            - item_per_key: returns a list with one item per key containing the list of values
                from all the fields
            - dict_per_field: returns a list of dictionaries with one dictionary per field with
                key-value pairs for the requested keys.
            - dict_per_key: returns a dictionary for each key containing the list of
                values from all the fields.

        remapping: dict, None
            A remapping dictionary passed to
            :obj:`GribField.get() <data.readers.grib.codes.GribField.get>`
            when getting the metadata values.
        patches: dict, None
            A dictionary of patches passed to
            :obj:`GribField.get() <data.readers.grib.codes.GribField.get>`
            when getting the metadata values.

        Returns
        -------
        list, tuple, dict, Any
            The returned value depends on the ``output`` parameter. See above.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.


        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.get("parameter.variable")
        ['2t', 'msl']
        >>> ds.get(["parameter.variable", "parameter.units"])
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.get(("parameter.variable", "parameter.units"))
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    # @abstractmethod
    # def get_as_dict(self, *args, group=False, remapping=None, patches=None, **kwargs):
    #     r"""Return the metadata values for each field.

    #     Parameters
    #     ----------
    #     *args: tuple
    #         Positional arguments defining the metadata keys. Passed to
    #         :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
    #     **kwargs: dict, optional
    #         Keyword arguments passed to
    #         :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

    #     Returns
    #     -------
    #     list
    #         List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

    #     Examples
    #     --------
    #     >>> import earthkit.data
    #     >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
    #     >>> ds.metadata("param")
    #     ['2t', 'msl']
    #     >>> ds.metadata("param", "units")
    #     [('2t', 'K'), ('msl', 'Pa')]
    #     >>> ds.metadata(["param", "units"])
    #     [['2t', 'K'], ['msl', 'Pa']]

    #     """
    #     pass

    @abstractmethod
    def metadata(self, *args, **kwargs):
        r"""Return the metadata values for each field.

        Parameters
        ----------
        *args: tuple
            Positional arguments defining the metadata keys. Passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`GribField.metadata() <data.readers.grib.codes.GribField.metadata>`

        Returns
        -------
        list
            List with one item per :obj:`GribField <data.readers.grib.codes.GribField>`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.metadata("param")
        ['2t', 'msl']
        >>> ds.metadata("param", "units")
        [('2t', 'K'), ('msl', 'Pa')]
        >>> ds.metadata(["param", "units"])
        [['2t', 'K'], ['msl', 'Pa']]

        """
        pass

    @abstractmethod
    def indices(self, squeeze=False):
        r"""Return the unique, sorted values for a set of metadata keys (see below)
        from all the fields. Individual keys can be also queried by :obj:`index`.

        Parameters
        ----------
        squeeze : False
            When True only returns the metadata keys that have more than one values.

        Returns
        -------
        dict
            Unique, sorted metadata values from all the
            :obj:`Field`\ s.

        See Also
        --------
        index

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.indices()
        {'class': ['od'], 'stream': ['oper'], 'levtype': ['pl'], 'type': ['an'],
        'expver': ['0001'], 'date': [20180801], 'time': [1200], 'domain': ['g'],
        'number': [0], 'levelist': [300, 400, 500, 700, 850, 1000],
        'param': ['t', 'u', 'v']}
        >>> ds.indices(squeeze=True)
        {'levelist': [300, 400, 500, 700, 850, 1000], 'param': ['t', 'u', 'v']}
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        By default :obj:`indices` uses the keys from the
        "mars" :xref:`eccodes_namespace`. Keys with no valid values are not included. Keys
        that :obj:`index` is called with are automatically added to the original set of keys
        used in :obj:`indices`.

        """
        pass

    @abstractmethod
    def index(self, key):
        r"""Return the unique, sorted values of the specified metadata ``key`` from all the fields.
        ``key`` will be automatically added to the keys returned by :obj:`indices`.

        Parameters
        ----------
        key : str
            Metadata key.

        Returns
        -------
        list
            Unique, sorted values of ``key`` from all the
            :obj:`Field`\ s.

        See Also
        --------
        index

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.index("level")
        [300, 400, 500, 700, 850, 1000]

        """
        return self._md_indices.index(key)

    @abstractmethod
    def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
        r"""Generate a list like summary using a set of metadata keys.

        Parameters
        ----------
        n: int, None
            The number of :obj:`Field`\ s to be
            listed. None means all the fields, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            Metadata keys used when ``namespace`` is None. If ``keys`` is None the following default
            set of keys will be used:  "centre", "shortName", "typeOfLevel", "level", "dataDate",
            "dataTime", "stepRange", "dataType", "number", "gridType". To specify a column title for each
            key in the output use a dict.
        extra_keys: list of str, dict, None
            List of additional keys. To specify a column title for each key in the output
            use a dict.
        namespace: str, list of str, None
            The namespace(s) to choose the ``keys`` from. When it is set ``keys`` are omitted.

        Returns
        -------
        Pandas DataFrame
            DataFrame with one row per :obj:`Field`.

        See Also
        --------
        head
        tail

        """
        pass

    @abstractmethod
    def head(self, n=5, **kwargs):
        r"""Generate a list like summary of the first ``n`` :obj:`Field`\ s.
        Same as calling :obj:`ls` with ``n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0) to be printed from the front.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        ls
        tail

        Notes
        -----
        The following calls are equivalent:

        .. code-block:: python

            ds.head()
            ds.head(5)
            ds.head(n=5)
            ds.ls(5)
            ds.ls(n=5)

        """
        pass

    @abstractmethod
    def tail(self, n=5, **kwargs):
        r"""Generate a list like summary of the last ``n`` :obj:`Field`\ s.
        Same as calling :obj:`ls` with ``-n``.

        Parameters
        ----------
        n: int, None
            The number of messages (``n`` > 0)  to be printed from the back.
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`ls`.

        Returns
        -------
        Pandas DataFrame
            See  :obj:`ls`.

        See Also
        --------
        head
        ls

        Notes
        -----
        The following calls are equivalent:

        .. code-block:: python

            ds.tail()
            ds.tail(5)
            ds.tail(n=5)
            ds.ls(-5)
            ds.ls(n=-5)

        """
        pass

    @abstractmethod
    def describe(self, *args, **kwargs):
        r"""Generate a summary of the fieldlist."""
        pass

    @abstractmethod
    def to_fieldlist(self, array_namespace=None, device=None, **kwargs):
        r"""Convert to a new :class:`FieldList`.

        Parameters
        ----------
        array_namespace: str, array_namespace or None
            The array namespace to be used. **New in version 0.19.0**.
        device: str or None
            The device where the array will be allocated. When it is
            :obj:`None` the default device is used. **New in version 0.19.0**.
        **kwargs: dict, optional
            ``kwargs`` are passed to :obj:`to_array` to
            extract the field values the resulting object will store.

        Returns
        -------
        :class:`SimpleFieldList`
            - a new fieldlist containing :class`ArrayField` fields

        Examples
        --------
        The following example will convert a fieldlist read from a file into a
        :class:`SimpleFieldList` storing single precision field values.

        >>> import numpy as np
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/tuv_pl.grib")
        >>> ds.path
        'docs/examples/tuv_pl.grib'
        >>> r = ds.to_fieldlist(array_namespace="numpy", dtype=np.float32)
        >>> r
        SimpleFieldList(fields=18)
        >>> hasattr(r, "path")
        False
        >>> r.to_numpy().dtype
        dtype('float32')

        """
        pass

    @abstractmethod
    def to_tensor(self, *args, **kwargs):
        pass

    @abstractmethod
    def cube(self, *args, **kwargs):
        pass

    @abstractmethod
    def default_encoder(self):
        pass

    @abstractmethod
    def _encode(self, encoder, **kwargs):
        """Double dispatch to the encoder"""
        pass

    @abstractmethod
    def normalise_key_values(self, **kwargs):
        pass

    def _unary_op(self, oper):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        return get_method(method).unary_op(oper, self)

    def _binary_op(self, oper, y):
        from earthkit.data.utils.compute import get_method

        method = "loop"
        r = get_method(method).binary_op(oper, self, y)
        return r
