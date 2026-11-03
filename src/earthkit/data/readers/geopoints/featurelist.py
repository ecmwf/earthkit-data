# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""FeatureList for geopoints data.

In block mode each feature is one geopoints block (the content of a ``#GEO`` file or one member of a
``#GEOPOINTSET``) and its metadata is the ``#METADATA`` section of the block.

In row mode each feature is one data row. Its metadata is the ``#METADATA`` section of the block the
row belongs to plus the columns of the row (the value of the row wins when a name is in both). The row
features are created on access, so a list with millions of rows is cheap to create.
"""

import functools
import logging
import operator

import numpy as np

from earthkit.data.featurelist.indexed import IndexFeatureListBase
from earthkit.data.featurelist.simple import SimpleFeatureListBase

LOG = logging.getLogger(__name__)

#: The modes accepted by ``to_featurelist()``.
FEATURELIST_MODES = ("block", "row")

_NO_DEFAULT = object()


def check_mode(mode):
    """Raise ValueError when ``mode`` is not one of :data:`FEATURELIST_MODES`."""
    if not isinstance(mode, str) or mode not in FEATURELIST_MODES:
        allowed = ", ".join(repr(m) for m in FEATURELIST_MODES)
        raise ValueError(f"Invalid featurelist mode={mode!r}. Allowed modes: {allowed}")


def make_featurelist(blocks, mode="block"):
    """Build the featurelist for the parser blocks ``blocks`` in the given ``mode``.

    Parameters
    ----------
    blocks: list of :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`
        The blocks, in order.
    mode: str
        "block" gives one feature per block. "row" gives one feature per data row of all the blocks,
        in order.

    Returns
    -------
    :class:`GeopointsFeatureList` or :class:`GeopointsRowFeatureList`
    """
    check_mode(mode)
    if mode == "block":
        return GeopointsFeatureList([GeopointsFeature(b) for b in blocks])
    return GeopointsRowFeatureList(blocks)


def _is_missing(x):
    """Return True for None and for NaN-like scalars (float NaN, NaT, pandas.NA)."""
    if x is None:
        return True
    if isinstance(x, float):
        return x != x
    if isinstance(x, (str, int)):
        return False
    try:
        import pandas as pd

        return bool(pd.isna(x))
    except (TypeError, ValueError):
        return False


def _per_key(value, n, name):
    """Broadcast ``value`` (a scalar or a list/tuple with one item or ``n`` items) to a list."""
    if isinstance(value, (list, tuple)):
        if len(value) == n:
            return list(value)
        if len(value) == 1:
            return [value[0]] * n
        raise ValueError(f"metadata: {name} must have the same number of items as the keys")
    return [value] * n


class _GeopointsFeatureBase:
    """The metadata API shared by the block and the row features.

    A subclass provides ``_get_single()``, ``_metadata_dict()``, ``default_ls_keys``, ``format`` and
    ``to_pandas()``.
    """

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        raise NotImplementedError

    def _metadata_dict(self):
        """Return the whole metadata as a new dict."""
        raise NotImplementedError

    def _get_fast(
        self,
        keys,
        default=None,
        astype=None,
        raise_on_missing=False,
        output=None,
        flatten_dict=False,
        remapping=None,
        collections=None,
    ):
        meth = self._get_single
        if remapping is not None:
            meth = remapping(meth)

        if keys is None:
            keys = []

        if isinstance(keys, str):
            result = meth(keys, default=default, astype=astype, raise_on_missing=raise_on_missing)
            if output is dict:
                result = {keys: result}
            return result

        keys = list(keys)
        astypes = _per_key(astype, len(keys), "astype")
        defaults = _per_key(default, len(keys), "default")
        values = [
            meth(k, default=d, astype=t, raise_on_missing=raise_on_missing) for k, t, d in zip(keys, astypes, defaults)
        ]
        if output is dict:
            return dict(zip(keys, values))
        if output is tuple:
            return tuple(values)
        return values

    def metadata(self, *keys, default=_NO_DEFAULT, astype=None):
        """Return the metadata of the feature.

        Parameters
        ----------
        *keys: str, list or tuple of str
            The metadata keys. Without keys the whole metadata is returned as a dict.
        default: Any, optional
            Value returned for a key that is not in the metadata. Without it a missing key raises
            KeyError. A single value is used for all the missing keys.
        astype: type, optional
            Type (or a callable such as ``int`` or ``str``) to convert the values into. For several
            keys it can be a list with one item per key.

        Returns
        -------
        dict, Any, list
            Without ``keys`` a copy of the metadata dict; changing it does not change the feature.
            For a single str the value of the key. For a list/tuple of str, or several str
            arguments, a list of values.

        Raises
        ------
        KeyError
            When a key is not in the metadata and ``default`` is not given.
        """
        if not keys:
            return self._metadata_dict()

        raise_on_missing = default is _NO_DEFAULT
        if raise_on_missing:
            default = None

        if len(keys) == 1 and isinstance(keys[0], str):
            return self._get_single(keys[0], default, astype=astype, raise_on_missing=raise_on_missing)

        flat = []
        for k in keys:
            if isinstance(k, str):
                flat.append(k)
            elif isinstance(k, (list, tuple)):
                flat.extend(k)
            else:
                raise ValueError(f"metadata: invalid key argument={k!r}")

        return self._get_fast(flat, default=default, astype=astype, raise_on_missing=raise_on_missing, output=list)

    def to_xarray(self, **kwargs):
        """Convert the points of the feature into an xarray object.

        The points are converted with :meth:`to_pandas` and then with
        :py:meth:`pandas.DataFrame.to_xarray`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.
        """
        return self.to_pandas().to_xarray(**kwargs)

    def _default_encoder(self):
        return None


class GeopointsFeature(_GeopointsFeatureBase):
    """One geopoints block.

    The metadata is the ``#METADATA`` section of the block (values converted to int, float or str as
    the parser does). The format, the columns and the number of points are not part of the
    metadata, they are available as properties.

    The ``format`` property is the geopoints format of the block: "TRADITIONAL", "XYV", "XY_VECTOR",
    "POLAR_VECTOR" or "NCOLS". The ``columns`` property is the list of the column names of the block
    in file order, as the parser gives them (``time`` is included where it exists, although the
    DataFrame merges it into ``date``). ``len(feature)`` is the number of points in the block.

    Parameters
    ----------
    block: :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`
        The parsed block.
    """

    def __init__(self, block):
        self._block = block
        self._metadata = dict(block.metadata)

    @property
    def format(self):
        return self._block.format

    @property
    def columns(self):
        return list(self._block.columns)

    def __len__(self):
        return len(self._block)

    def __repr__(self):
        return f"{self.__class__.__name__}(format={self.format!r}, points={len(self)}, metadata={self._metadata!r})"

    @property
    def default_ls_keys(self):
        """The metadata keys (list of str), used as the default keys of ``ls()``."""
        return list(self._metadata)

    # -- metadata ------------------------------------------------------------------------------

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        try:
            v = self._metadata[key]
        except KeyError:
            if raise_on_missing:
                raise KeyError(f"Key {key!r} not found in the geopoints metadata") from None
            return default

        if astype is not None:
            return astype(v)
        return v

    def _metadata_dict(self):
        return dict(self._metadata)

    # -- data ----------------------------------------------------------------------------------

    def to_pandas(self):
        """Return the points of the block as a new :py:class:`pandas.DataFrame`."""
        return self._block.to_pandas()


def _to_python(v):
    """Convert a numpy scalar into a plain Python value (dates become :py:class:`pandas.Timestamp`)."""
    if isinstance(v, np.datetime64):
        import pandas as pd

        return pd.NaT if np.isnat(v) else pd.Timestamp(v)
    if isinstance(v, np.generic):
        return v.item()
    return v


class _RowSource:
    """What the row features of one block share: the frame, its columns as numpy arrays and the metadata."""

    def __init__(self, block):
        self.block = block
        # The frame is only read. to_pandas() would copy it.
        self.frame = block._frame
        self.metadata = dict(block.metadata)
        self.names = list(self.frame.columns)
        self.columns = frozenset(self.names)
        self.keys = list(dict.fromkeys([*self.metadata, *self.names]))
        self._arrays = {}

    def __len__(self):
        return len(self.frame)

    def array(self, name):
        a = self._arrays.get(name)
        if a is None:
            a = self._arrays[name] = self.frame[name].to_numpy()
        return a

    def __getstate__(self):
        return {"block": self.block}

    def __setstate__(self, state):
        self.__init__(state["block"])


class GeopointsRowFeature(_GeopointsFeatureBase):
    """One data row of a geopoints block.

    The metadata is the ``#METADATA`` section of the block plus the columns of the row (``latitude``,
    ``longitude``, ``level``, ``date``, ``value``, ``stnid``, ...). When a name is in both, the value
    of the row is used. The values are plain Python scalars: numbers are int or float (a missing
    number is NaN), text is str (a missing ``stnid`` is None) and the dates are
    :py:class:`pandas.Timestamp`.

    The ``format`` property is the geopoints format of the block and the ``row`` property is the
    position of the row in the block.

    Parameters
    ----------
    block: :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`
        The parsed block.
    row: int
        The position of the row in the block. A negative value counts from the end.
    """

    def __init__(self, block, row, *, _source=None):
        if _source is None:
            _source = _RowSource(block)
            n = len(_source)
            if not -n <= row < n:
                raise IndexError(f"row {row} is out of range for a block with {n} rows")
            if row < 0:
                row += n
        self._source = _source
        self._row = row

    @property
    def format(self):
        return self._source.block.format

    @property
    def row(self):
        return self._row

    def __repr__(self):
        return f"{self.__class__.__name__}(format={self.format!r}, row={self._row}, metadata={self._metadata_dict()!r})"

    @property
    def default_ls_keys(self):
        """The metadata keys (list of str), used as the default keys of ``ls()``."""
        return list(self._source.keys)

    # -- metadata ------------------------------------------------------------------------------

    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False):
        src = self._source
        if key in src.columns:
            v = _to_python(src.array(key)[self._row])
        else:
            try:
                v = src.metadata[key]
            except KeyError:
                if raise_on_missing:
                    raise KeyError(f"Key {key!r} not found in the geopoints row metadata") from None
                return default

        if astype is not None:
            return astype(v)
        return v

    def _metadata_dict(self):
        src = self._source
        d = dict(src.metadata)
        row = self._row
        for name in src.names:
            d[name] = _to_python(src.array(name)[row])
        return d

    # -- data ----------------------------------------------------------------------------------

    def to_pandas(self):
        """Return the row as a :py:class:`pandas.DataFrame` with one row.

        It has the columns and dtypes of the block and the index 0.
        """
        return self._source.frame.iloc[self._row : self._row + 1].reset_index(drop=True)


class GeopointsFeatureListMixin:
    """Behaviour shared by the geopoints featurelists.

    It only relies on ``len()``, indexing, iteration and ``new_mask_index()``, so it can be used with
    any list of geopoints features. The metadata of the features is read with plain keys (not the
    "component.key" form of the fieldlists), therefore ``metadata()`` is overridden.
    """

    def metadata(self, *args, **kwargs):
        """Return the metadata of each feature.

        Parameters
        ----------
        *args, **kwargs
            Passed to the ``metadata()`` method of the features.

        Returns
        -------
        list
            One item per feature.
        """
        return [f.metadata(*args, **kwargs) for f in self]

    def ls(self, n=None, keys="default", extra_keys=None, collections=None):
        """Return a summary of the features as a :py:class:`pandas.DataFrame`.

        Parameters
        ----------
        n: int, None
            The number of features to show. For ``n > 0`` the first ``n`` features, for ``n < 0`` the
            last ``-n`` features are shown. By default all the features are shown.
        keys: str, list, tuple, dict
            The metadata keys of the columns. With "default" the columns are the union of the
            metadata keys of the features that are shown, in the order they are first seen. A
            feature without a key has None in its column.
        extra_keys: str, list, tuple, dict, optional
            Columns added to ``keys``.
        collections: str, list, tuple, optional
            Not used for geopoints.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            One row per feature shown.
        """
        if isinstance(keys, str) and keys == "default":
            keys = self._default_ls_keys_of(n)
        return super().ls(n=n, keys=keys, extra_keys=extra_keys, collections=collections)

    def _default_ls_keys_of(self, n):
        # Only the features that are shown are read: head() of a huge list must stay cheap. The
        # positions are those of IndexFeatureListBase.ls().
        if n is not None and (not isinstance(n, int) or n == 0):
            # invalid, ls() raises the error
            return self._default_ls_keys()

        num = len(self)
        if n is None:
            pos = range(num)
        elif n > 0:
            pos = range(min(num, n))
        else:
            pos = range(num - min(num, -n), num)

        keys = {}
        for i in pos:
            keys.update(dict.fromkeys(self[i].default_ls_keys))
        return list(keys)

    def order_by(self, *args, remapping=None, patch=None, **kwargs):
        """Change the order of the features.

        It works as :meth:`earthkit.data.core.index.Index.order_by`, except that missing values
        (None, NaN, or a key that is not in the metadata) always go last, whether the order is
        ascending or descending (as :py:meth:`pandas.DataFrame.sort_values` does). This rule belongs
        to the built-in orders ("ascending", "descending" and a list of values). A callable
        comparator is given the raw values, missing ones included, and has to handle them itself.

        Parameters
        ----------
        *args: tuple
            Positional arguments specifying the metadata keys to perform the ordering on.
        remapping: dict
            Defines new metadata keys from existing ones, as for ``sel()``.
        patch: dict
            A dictionary of patches applied to the metadata values.
        **kwargs: dict, optional
            Keys to order by with "ascending", "descending", a list of values or a callable.

        Returns
        -------
        object
            A new featurelist with the reordered features.
        """
        from earthkit.data.core.index import Order
        from earthkit.data.core.order import build_remapping, normalise_order_by

        kwargs = normalise_order_by(*args, **kwargs)
        remapping = build_remapping(remapping, patch)

        if not kwargs:
            return self

        order = Order(kwargs, remapping=remapping)
        if order.is_empty:
            return self

        # A user supplied callable is responsible for the missing values itself.
        order.actions = {
            k: action if callable(kwargs[k]) else self._missing_last(action) for k, action in order.actions.items()
        }

        features = list(self)

        def cmp(i, j):
            return order.compare_elements(features[i], features[j])

        indices = sorted(range(len(features)), key=functools.cmp_to_key(cmp))
        return self.new_mask_index(self, indices)

    @staticmethod
    def _missing_last(action):
        # The descending action is the negated ascending one, so the missing values are handled
        # before the direction is applied.
        def wrapped(a, b):
            a_missing = _is_missing(a)
            b_missing = _is_missing(b)
            if a_missing or b_missing:
                if a_missing and b_missing:
                    return 0
                return 1 if a_missing else -1
            return action(a, b)

        return wrapped

    def to_pandas(self):
        """Return the points of all the features as one :py:class:`pandas.DataFrame`.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            The frames of the features stacked in order with ``ignore_index=True``. Columns missing in
            a feature are filled with NaN. An empty list gives an empty DataFrame.
        """
        import pandas

        frames = [f.to_pandas() for f in self]
        if not frames:
            return pandas.DataFrame()
        return pandas.concat(frames, ignore_index=True)

    def to_xarray(self, **kwargs):
        """Convert the points of all the features into an xarray object.

        The features are converted with :meth:`to_pandas` and then with
        :py:meth:`pandas.DataFrame.to_xarray`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.
        """
        return self.to_pandas().to_xarray(**kwargs)

    def to_data_object(self):
        from earthkit.data.data.featurelist import FeatureListData

        return FeatureListData(self)

    def _default_encoder(self):
        return None

    def __repr__(self):
        return f"{self.__class__.__name__}(len={len(self)})"


class GeopointsFeatureList(GeopointsFeatureListMixin, SimpleFeatureListBase):
    """A list of :class:`GeopointsFeature` objects held in memory.

    By default ``ls()``, ``head()`` and ``tail()`` show the union of the metadata keys of the features
    that are shown.

    Parameters
    ----------
    features: list of :class:`GeopointsFeature`, optional
        The features. Slices and the results of ``sel()`` and ``order_by()`` are built from a plain list
        of features in the same way.
    """

    def __init__(self, features=None):
        self.__features = list(features) if features is not None else []

    @property
    def _features(self):
        return self.__features

    def __getstate__(self) -> dict:
        return {"_features": self._features}

    def __setstate__(self, state: dict):
        self.__init__(state.pop("_features"))


class GeopointsRowFeatureList(GeopointsFeatureListMixin, IndexFeatureListBase):
    """A list with one :class:`GeopointsRowFeature` per data row of the geopoints blocks.

    The row features are not created up front: a feature is built when it is accessed (by indexing or
    iteration), so creating the list and ``len()`` are cheap even for millions of rows. The same holds
    for slices and for the results of ``sel()`` and ``order_by()``: they are views that only hold the
    positions of the selected rows and have the same type. Blocks without rows add no feature.

    Parameters
    ----------
    blocks: list of :class:`~earthkit.data.readers.geopoints.parser.GeopointsBlock`
        The blocks, in order. They can come from several files.

    Notes
    -----
    ``to_pandas()`` of the whole list stacks the frames of the blocks (``ignore_index=True``); for a
    selection it takes the rows of the selected blocks in the order of the selection, so a selection
    that jumps often between blocks is slower than one in block order.
    """

    def __init__(self, blocks=None):
        self._blocks = list(blocks) if blocks is not None else []
        self._sources = [_RowSource(b) for b in self._blocks if len(b) > 0]
        # offsets[i] is the global position of the first row of block i
        self._offsets = np.cumsum([0] + [len(s) for s in self._sources], dtype=np.int64)
        # None: all the rows; otherwise the (global) positions of the rows, in order
        self._indices = None

    def _derive(self, indices):
        new = object.__new__(type(self))
        new._blocks = self._blocks
        new._sources = self._sources
        new._offsets = self._offsets
        new._indices = indices
        return new

    def __len__(self):
        if self._indices is not None:
            return len(self._indices)
        return int(self._offsets[-1])

    def _feature(self, g):
        # g: global position of the row in the blocks
        offsets = self._offsets
        b = int(np.searchsorted(offsets, g, side="right")) - 1
        return GeopointsRowFeature(None, int(g - offsets[b]), _source=self._sources[b])

    def _getitem(self, n):
        try:
            n = operator.index(n)
        except TypeError:
            raise TypeError(
                f"{type(self).__name__} indices must be integers or slices, not {type(n).__name__}"
            ) from None

        size = len(self)
        if n < 0:
            n += size
        if not 0 <= n < size:
            raise IndexError("index out of range")

        g = n if self._indices is None else self._indices[n]
        return self._feature(g)

    def __iter__(self):
        if self._indices is None:
            for src in self._sources:
                for row in range(len(src)):
                    yield GeopointsRowFeature(None, row, _source=src)
        else:
            for g in self._indices.tolist():
                yield self._feature(g)

    def _from_ndarray(self, a):
        # The default converts the array into a list; the array is checked and used as it is.
        return self.new_mask_index(self, a)

    @staticmethod
    def _positions(indices):
        """Convert a sequence of positions into an int64 array.

        As for a Python list, every position must be an integer (anything accepted by
        :func:`operator.index`, so also numpy integers and bool); otherwise TypeError is raised.
        """
        if isinstance(indices, np.ndarray):
            if indices.ndim != 1:
                raise TypeError(f"indices must be a 1-dimensional array, got {indices.ndim} dimension(s)")
            if indices.size == 0:
                return np.empty(0, dtype=np.int64)
            kind = indices.dtype.kind
            if kind in "iub":
                if kind == "u" and indices.dtype.itemsize == 8 and indices.max() > np.iinfo(np.int64).max:
                    raise IndexError("index out of range")
                # a boolean array is used as 0/1 positions, as for a Python list
                return indices.astype(np.int64, copy=False)
            if kind != "O":
                raise TypeError(f"indices must be integers, not {indices.dtype}")
            indices = indices.tolist()

        try:
            return np.array([operator.index(i) for i in indices], dtype=np.int64)
        except TypeError as e:
            raise TypeError(f"indices must be integers: {e}") from None
        except OverflowError:
            raise IndexError("index out of range") from None

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs, indices = args
        size = len(fs)

        if isinstance(indices, range):
            idx = np.arange(indices.start, indices.stop, indices.step, dtype=np.int64)
        else:
            idx = cls._positions(indices)

        idx = np.where(idx < 0, idx + size, idx)
        if idx.size and (idx.min() < 0 or idx.max() >= size):
            raise IndexError("index out of range")

        if fs._indices is not None:
            idx = fs._indices[idx]
        return fs._derive(idx)

    def mutate_source(self):
        return self

    def to_pandas(self):
        """Return the points of all the features as one :py:class:`pandas.DataFrame`.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            For the whole list the frames of the blocks, stacked in order; the result is the same as
            the ``to_pandas()`` of the data. For a selection the rows of the selected features in
            their order. In both cases ``ignore_index=True`` is used and columns missing in a block
            are filled with NaN. An empty list gives an empty DataFrame.
        """
        import pandas

        if self._indices is None:
            frames = [b._frame for b in self._blocks]
            if not frames:
                return pandas.DataFrame()
            if len(frames) == 1:
                return frames[0].copy()
            return pandas.concat(frames, ignore_index=True)

        idx = self._indices
        if len(idx) == 0:
            return pandas.DataFrame()

        # Consecutive rows of the same block are taken together.
        blocks = np.searchsorted(self._offsets, idx, side="right") - 1
        rows = idx - self._offsets[blocks]
        cuts = np.flatnonzero(np.diff(blocks)) + 1
        starts = [0, *cuts.tolist()]
        stops = [*cuts.tolist(), len(idx)]
        frames = [self._sources[blocks[a]].frame.iloc[rows[a:b]] for a, b in zip(starts, stops)]
        if len(frames) == 1:
            return frames[0].reset_index(drop=True)
        return pandas.concat(frames, ignore_index=True)

    def __getstate__(self) -> dict:
        return {"blocks": self._blocks, "indices": self._indices}

    def __setstate__(self, state: dict):
        self.__init__(state["blocks"])
        self._indices = state["indices"]
