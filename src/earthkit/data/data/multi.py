# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,  # noqa: F401
)

import deprecation

from . import Data, SimpleData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]
    import xarray  # type: ignore[import]

    from earthkit.data.core.fieldlist import FieldList


class MultiData(SimpleData):
    """Represent multiple ``Data`` objects that cannot be reduced to a single, type-specific one.

    When :func:`earthkit.data.from_source` combines multiple inputs (e.g. a list of files), it first
    attempts to mutate them into a single, type-specific :class:`~earthkit.data.data.Data` object (e.g.
    ``GribData`` for a set of GRIB files) -- see :ref:`mergers` for how this merging works. A
    ``MultiData`` is returned instead whenever that is not possible, which happens in two situations:

    - the inputs are of mixed types and cannot be merged into a single typed object (e.g. one GRIB file
      and one NetCDF file);
    - the inputs are all of the same type, but that type does not support merging multiple inputs into
      one object (e.g. ``CSVData`` wraps a single reader per file, so multiple CSV files always yield a
      ``MultiData``).

    A ``MultiData`` holds a list of sub-items, each itself a ``Data`` object (see :obj:`_data`) -- unlike
    :class:`~earthkit.data.sources.multi.MultiSource`, it does not wrap a single underlying source:
    :obj:`_source` is always None, kept only so that code checking for a ``_source`` attribute (as
    :class:`~earthkit.data.sources.multi.MultiSource` does when deciding whether to drop an ignorable
    sub-item) sees the attribute present without mistaking a ``MultiData`` for something with one real
    underlying source. Iterating over a ``MultiData`` (:obj:`__iter__`) recursively flattens any nested
    ``MultiData`` sub-item, which is what :obj:`path` uses to collect every leaf path; the ``to_*``
    conversions below, by contrast, work directly over :obj:`_data` one level deep, treating a nested
    ``MultiData`` sub-item as a single (already convertible) ``Data`` object rather than flattening it.
    """

    _TYPE_NAME = "Multi"

    def __init__(self, *data, merger=None):
        """Initialize a MultiData object.

        Parameters
        ----------
        *data : :ref:`Data object <data-object>`, or list/tuple of them
            The sub-items to combine, as positional arguments. A ``list`` or ``tuple`` item is flattened
            one level, so both ``MultiData(a, b)`` and ``MultiData([a, b])`` produce the same two-item
            :obj:`_data`; each element of such a list/tuple must itself be a ``Data`` object, not a
            further nested list/tuple. Every item, once flattened, must be a ``Data`` object -- unlike
            :class:`~earthkit.data.sources.multi.MultiSource`, a raw ``Source`` is not accepted directly
            here.
        merger : object, str, tuple, or None, optional
            The merger to use for the ``to_*`` conversions below, stored as :obj:`_merger` and passed
            straight through to :func:`earthkit.data.mergers.make_merger` -- see
            :class:`~earthkit.data.sources.multi.MultiSource` for the accepted values.

        Raises
        ------
        ValueError
            If, once flattened, an item in ``data`` is not a ``Data`` object.
        """
        self._data = []
        for d in data:
            if isinstance(d, (list, tuple)):
                self._data.extend(d)
            else:
                self._data.append(d)

        self._sources_legacy = [d._source for d in self._data if hasattr(d, "_source")]
        self._merger = merger
        self._source = None

        for d in self._data:
            if not isinstance(d, Data):
                raise ValueError(f"All inputs must be Data objects. Invalid input type: {type(d)}")

    def __iter__(self):
        """Iterate over all sub-items, recursively expanding nested ``MultiData`` objects.

        Every :ref:`Data object <data-object>` other than ``MultiData`` is not iterable, so an item that
        is not itself a ``MultiData`` is yielded as is; an item that is a ``MultiData`` is iterated into
        recursively instead, flattening the whole tree into a single sequence.

        Yields
        ------
        :ref:`Data object <data-object>`
            Each leaf ``Data`` item, or a non-leaf item that is not itself a ``MultiData``.
        """
        for d in self._data:
            if isinstance(d, MultiData):
                yield from d
            else:
                yield d

    @property
    def available_types(self) -> list[str]:
        """list[str]: The union of the ``available_types`` of every sub-item (see :obj:`_data`).

        Falls back to an empty list rather than raising if computing it fails for any reason.
        """
        types = set()
        try:
            for d in self._data:
                r = d.available_types
                types.update(r)
            return sorted(types)
        except Exception:
            pass

        return list()

    @property
    @deprecation.deprecated(
        deprecated_in="1.1.0",
        removed_in=None,
        details=(
            "The 'sources' property is deprecated and will be removed in a future release. "
            "Access to the underlying sources in MultiData is no longer part of the public API."
        ),
    )
    def sources(self) -> Any:
        """Deprecated. Access to the underlying sources is no longer part of the public API."""
        return self._sources_legacy

    def _data_objects(self, match: str | None = None):
        """Return the ``Data`` object for each item in :obj:`_data`, optionally filtered by supported type.

        Every item in :obj:`_data` is already a ``Data`` object (see :obj:`__init__`), so this operates
        one level deep, without recursing into a nested :class:`MultiData` item -- it is returned as a
        single ``Data`` object like any other, not expanded into its own sub-items (unlike :obj:`__iter__`).
        The ``if not isinstance(s, Data)`` branch below is currently unreachable given that guarantee; it
        is kept defensively in case a future caller passes something else into :obj:`_data` directly.

        Parameters
        ----------
        match : str, optional
            When given, only items whose :obj:`~earthkit.data.data.Data.available_types` includes this
            type name are returned.

        Returns
        -------
        list of :ref:`Data object <data-object>`
        """
        res = []
        # print("data_objects called")
        for s in self._data:
            # print(f"Processing data item: {s}")
            if not isinstance(s, (Data)):
                d = s.to_data_object()
            else:
                d = s
            # print(f".  d: {d}")
            if isinstance(d, Data):
                if match is None or match in s.available_types:
                    res.append(d)
            # print(f".  Current result list: {len(res)}")

        return res

    def describe(self) -> Any:
        """Provide a description of the MultiData.

        Note that, unlike some other ``Data`` subclasses' ``describe()``, the resulting
        :class:`~earthkit.data.utils.summary.DataDescriber` is built with only a title and
        :obj:`available_types` -- :obj:`path` is not included.

        Returns
        -------
        :class:`earthkit.data.utils.summary.DataDescriber`
            A ``DataDescriber`` with the title ``"multi data"`` and :obj:`available_types`.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="multi data", types=self.available_types)

    @property
    def path(self) -> str | list[str] | None:
        """list[str]: The paths of every leaf sub-item, flattened recursively (see :obj:`__iter__`).

        For each leaf item, its own ``path`` is collected: extended into the result if it is itself a
        list, appended otherwise. A leaf item whose ``path`` raises is silently skipped rather than
        failing the whole property.
        """
        r = []
        for s in self:
            try:
                p = s.path
                if isinstance(p, list):
                    r.extend(p)
                else:
                    r.append(p)
            except Exception:
                pass

        return r

    def to_fieldlist(self, *args, **kwargs) -> FieldList:
        """Convert into a FieldList.

        Only the sub-items (see :obj:`_data`) that support ``"fieldlist"`` conversion are used; the
        others are silently left out. The merger to combine them with is built from :obj:`_merger` (see
        :func:`earthkit.data.mergers.make_merger`).

        Parameters
        ----------
        *args
            Currently unused.
        **kwargs
            Keyword arguments passed to the merger's ``to_fieldlist`` method.

        Returns
        -------
        :py:class:`earthkit.data.core.fieldlist.FieldList`
            A merged FieldList containing data from all sub-items that support it.

        Raises
        ------
        ValueError
            If no sub-item supports ``"fieldlist"`` conversion, or if the merger could not produce a
            fieldlist.
        """
        if "fieldlist" not in self.available_types:
            raise ValueError(
                "Cannot convert this MultiData object to a FieldList. None of the objects support FieldList conversion."
            )
        data = self._data_objects(match="fieldlist")
        if not data:
            raise ValueError("No suitable sources available for FieldList conversion.")

        from earthkit.data.mergers import make_merger

        merged = make_merger(self._merger, data).to_fieldlist(**kwargs)
        if merged is not None:
            return merged.mutate()

        raise ValueError("Cannot convert this MultiData object to a fieldlist")

    def to_xarray(self, *args, xarray_open_mfdataset_kwargs=None, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        The conversion is performed by using :py:func:`xarray.open_mfdataset`, merging only the sub-items
        (see :obj:`_data`) that support ``"xarray"`` conversion (via :obj:`_data_objects`); the others are
        silently left out.

        Parameters
        ----------
        *args
            Unused.
        xarray_open_mfdataset_kwargs : dict or None, optional
            Keyword arguments passed to :py:func:`xarray.open_mfdataset`. When given (and non-empty), this
            is used instead of ``**kwargs`` below -- see there.
        **kwargs
            Keyword arguments passed to :py:func:`xarray.open_mfdataset`. Ignored whenever
            ``xarray_open_mfdataset_kwargs`` is given and non-empty.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing data from all objects in the MultiData.

        Raises
        ------
        ValueError
            If no sub-item supports ``"xarray"`` conversion.

        Warns
        -----
        UserWarning
            If :obj:`_merger` is set and options were also given, since the merger may then ignore them.
        """
        if "xarray" not in self.available_types:
            raise ValueError(
                "Cannot convert this MultiData object to Xarray. None of the objects support Xarray conversion."
            )

        data = self._data_objects(match="xarray")
        if not data:
            raise ValueError("No suitable sources available for Xarray conversion.")

        if xarray_open_mfdataset_kwargs:
            options = dict(xarray_open_mfdataset_kwargs=xarray_open_mfdataset_kwargs)
        else:
            options = dict(kwargs)

        from earthkit.data.mergers import make_merger

        if self._merger and options:
            import warnings

            warnings.warn(
                "There seems to be a merger defined for the source, but additional options were provided. "
                "These options might be ignored."
            )

        return make_merger(self._merger, data).to_xarray(**options)

    def to_pandas(self, comment="#", pandas_read_csv_kwargs=None) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Only the sub-items (see :obj:`_data`) that support ``"pandas"`` conversion are used (via
        :obj:`_data_objects`); the others are silently left out.

        Parameters
        ----------
        comment : str, default "#"
            The character that represents a comment line in a CSV file, applied to every CSV sub-item.
            Ignored if ``comment`` is already set in ``pandas_read_csv_kwargs``.
        pandas_read_csv_kwargs : dict or None, optional
            Keyword arguments passed to :func:`pandas.read_csv` for every CSV sub-item.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the data from all objects in the MultiData.

        Raises
        ------
        ValueError
            If no sub-item supports ``"pandas"`` conversion.

        Warns
        -----
        UserWarning
            If :obj:`_merger` is set and ``pandas_read_csv_kwargs`` was also given, since the merger may
            then ignore it.
        """
        if "pandas" not in self.available_types:
            raise ValueError(
                "Cannot convert this MultiData object to Pandas. None of the objects support Pandas conversion."
            )

        data = self._data_objects(match="pandas")
        if not data:
            raise ValueError("No suitable sources available for Pandas conversion.")

        pandas_read_csv_kwargs = dict(pandas_read_csv_kwargs) if pandas_read_csv_kwargs is not None else {}
        if "comment" not in pandas_read_csv_kwargs:
            pandas_read_csv_kwargs["comment"] = comment

        if pandas_read_csv_kwargs:
            options = dict(pandas_read_csv_kwargs=pandas_read_csv_kwargs)
        else:
            options = dict(pandas_read_csv_kwargs={})

        from earthkit.data.mergers import make_merger

        if self._merger and options:
            import warnings

            warnings.warn(
                "There seems to be a merger defined for the source, but additional options were provided. "
                "These options might be ignored."
            )

        return make_merger(self._merger, data).to_pandas(**options)

    def to_geopandas(self, *args, **kwargs):
        """Convert into a GeoPandas GeoDataFrame.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to GeoPandas is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to geopandas is not implemented")

    def to_geojson(self, *args, **kwargs) -> dict:
        """Convert into GeoJSON format.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to GeoJSON is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to geojson is not implemented")

    def to_featurelist(self, *args, **kwargs):
        """Convert into a FeatureList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to FeatureList is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to featurelist is not implemented")

    def to_numpy(self, *args, **kwargs):
        """Convert into a NumPy array.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to NumPy is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to numpy is not implemented")

    def to_array(self, *args, **kwargs):
        """Convert into an array of a given array-like type.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Raises
        ------
        NotImplementedError
            Conversion of MultiData to array is not implemented.
        """
        raise NotImplementedError("Conversion of MultiData to array is not implemented")
