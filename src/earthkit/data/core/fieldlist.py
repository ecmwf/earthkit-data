# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

import deprecation

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
        to_latlon
        to_points
        to_numpy
        values

        """
        pass

    @abstractmethod
    def datetime(self):
        r"""Return the unique, sorted list of dates and times in the fieldlist.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds.datetime()
        {'base_time': [datetime.datetime(2020, 12, 21, 12, 0)],
        'valid_time': [
            datetime.datetime(2020, 12, 21, 12, 0),
            datetime.datetime(2020, 12, 21, 15, 0),
            datetime.datetime(2020, 12, 21, 18, 0),
            datetime.datetime(2020, 12, 21, 21, 0),
            datetime.datetime(2020, 12, 23, 12, 0)]}

        """

    @property
    @abstractmethod
    def geography(self):
        pass

    @abstractmethod
    def to_latlon(self, index=None, **kwargs):
        r"""Return the latitudes/longitudes shared by all the fields.

        Parameters
        ----------
        index: array indexing object, optional
            The index of the latitudes/longitudes to be extracted. When it is None
            all the values are extracted.
        **kwargs: dict, optional
            Keyword arguments passed to
            :meth:`Field.to_latlon() <data.core.fieldlist.Field.to_latlon>`

        Returns
        -------
        dict
            Dictionary with items "lat" and "lon", containing the arrays of the latitudes and
            longitudes, respectively.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> for f in ds:
        ...     print(f.shape)
        ...
        (11, 19)
        (11, 19)
        >>> r = ds.to_latlon()
        >>> for k, v in r.items():
        ...     print(f"{k}: shape={v.shape}")
        ...
        lat: shape=(11, 19)
        lon: shape=(11, 19)
        >>> r["lon"][:2]
        array([[-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.],
        [-27., -23., -19., -15., -11.,  -7.,  -3.,   1.,   5.,   9.,  13.,
         17.,  21.,  25.,  29.,  33.,  37.,  41.,  45.]])

        """

    @abstractmethod
    def to_points(self, **kwargs):
        r"""Return the geographical coordinates shared by all the fields in
        the data's original Coordinate Reference System (CRS).

        Parameters
        ----------
        **kwargs: dict, optional
            Keyword arguments passed to
            :obj:`Field.to_points() <data.core.fieldlist.Field.to_points>`

        Returns
        -------
        dict
            Dictionary with items "x" and "y", containing the arrays of the x and
            y coordinates, respectively.

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry.
        """
        pass

    @abstractmethod
    def bounding_box(self):
        pass

    @abstractmethod
    def projection(self):
        r"""Return the projection information shared by all the fields.

        Returns
        -------
        :obj:`Projection`

        Raises
        ------
        ValueError
            When not all the fields have the same grid geometry

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.projection()
        <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
        Name: unknown
        Axis Info [cartesian]:
        - E[east]: Easting (unknown)
        - N[north]: Northing (unknown)
        - h[up]: Ellipsoidal height (metre)
        Area of Use:
        - undefined
        Coordinate Operation:
        - name: unknown
        - method: Equidistant Cylindrical
        Datum: Unknown based on WGS 84 ellipsoid
        - Ellipsoid: WGS 84
        - Prime Meridian: Greenwich
        >>> ds.projection().to_proj_string()
        '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
        """
        pass

    @abstractmethod
    def get(self, *keys, remapping=None, patches=None, **kwargs):
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
    def get_as_dict(self, *args, group=False, remapping=None, patches=None, **kwargs):
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
            listed. None means all the messages, ``n > 0`` means fields from the front, while
            ``n < 0`` means fields from the back of the fieldlist.
        keys: list of str, dict, None
            Metadata keys. If it is None the following default set of keys will be used:  "centre",
            "shortName", "typeOfLevel", "level", "dataDate", "dataTime", "stepRange", "dataType",
            "number", "gridType". To specify a column title for each key in the output use a dict.
        extra_keys: list of str, dict, None
            List of additional keys to ``keys``. To specify a column title for each key in the output
            use a dict.
        namespace: str, None
            The namespace to choose the ``keys`` from. When it is set ``keys`` and
            ``extra_keys`` are omitted.

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
    def to_fieldlist(self, array_backend=None, **kwargs):
        r"""Convert to a new :class:`FieldList`.

        Parameters
        ----------
        array_backend: str, module, :obj:`ArrayBackend`
            Specifies the array backend for the generated :class:`FieldList`. The array
            type must be supported by :class:`ArrayBackend`.

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
        >>> r = ds.to_fieldlist(array_backend="numpy", dtype=np.float32)
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

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def save(self, filename, append=False, **kwargs):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str, optional
            The target file path, if not defined attempts will be made to detect the filename
        append: bool, optional
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists. Default is False
        **kwargs: dict, optional
            Other keyword arguments passed to :obj:`write`.

        See Also
        --------
        :obj:`write`
        :meth:`GribFieldList.save() <data.readers.grib.index.GribFieldList.save>`
        :meth:`SimpleFieldList.save() <data.indexing.fieldlist.SimpleFieldList.save>`

        """
        pass

    @deprecation.deprecated(deprecated_in="0.13.0", removed_in=None, details="Use to_target() instead")
    def write(self, f, **kwargs):
        r"""Write all the fields to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to the underlying field implementation.

        See Also
        --------
        read

        """
        pass
