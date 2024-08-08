# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.readers.grib.pandas import PandasMixIn
from earthkit.data.readers.grib.xarray import XarrayMixIn
from earthkit.data.utils.array import get_backend

LOG = logging.getLogger(__name__)


class ArrayField(Field):
    r"""Represent a field consisting of an array and metadata object.

    Parameters
    ----------
    array: array
        Array storing the values of the field
    metadata: :class:`Metadata`
        Metadata object describing the field metadata.
    array_backend: str, ArrayBackend
        Array backend. Must match the type of ``array``.
    """

    def __init__(self, array, metadata, array_backend):
        super().__init__(array_backend, raw_values_backend=array_backend, metadata=metadata)
        self._array = array

    def _values(self, dtype=None):
        """Native array type"""
        if dtype is None:
            return self._array
        else:
            return self.array_backend.array_ns.astype(self._array, dtype, copy=False)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def write(self, f, **kwargs):
        r"""Write the field to a file object.

        Parameters
        ----------
        f: file object
            The target file object.
        **kwargs: dict, optional
            Other keyword arguments passed to :meth:`data.writers.grib.GribWriter.write`.
        """
        from earthkit.data.writers import write

        write(f, self.to_numpy(flatten=True), self._metadata, **kwargs)


class ArrayFieldListCore(PandasMixIn, XarrayMixIn, FieldList):
    def __init__(self, array, metadata, *args, array_backend=None, **kwargs):
        self._array = array
        self._metadata = metadata

        if not isinstance(self._metadata, list):
            self._metadata = [self._metadata]

        # get backend and check consistency
        array_backend = get_backend(self._array, guess=array_backend, strict=True)

        FieldList.__init__(self, *args, array_backend=array_backend, **kwargs)

        if self.array_backend.is_native_array(self._array):
            if self._array.shape[0] != len(self._metadata):
                # we have a single array and a single metadata
                if len(self._metadata) == 1 and self._shape_match(
                    self._array.shape, self._metadata[0].geography.shape()
                ):
                    self._array = self.array_backend.array_ns.stack([self._array])
                else:
                    raise ValueError(
                        (
                            f"first array dimension ({self._array.shape[0]}) differs "
                            f"from number of metadata objects ({len(self._metadata)})"
                        )
                    )
        elif isinstance(self._array, list):
            if len(self._array) != len(self._metadata):
                raise ValueError(
                    (
                        f"array len ({len(self._array)}) differs "
                        f"from number of metadata objects ({len(self._metadata)})"
                    )
                )

            for i, a in enumerate(self._array):
                if not self.array_backend.is_native_array(a):
                    raise ValueError(
                        (
                            f"All array element must be an {self.array_backend.array_name}."
                            " Type at position={i} is {type(a)}"
                        )
                    )

        else:
            raise TypeError(
                (
                    f"array must be an {self.array_backend.array_name} or a"
                    f" list of {self.array_backend.array_name}s"
                )
            )

        # hide internal metadata related to values
        self._metadata = [md._hide_internal_keys() for md in self._metadata]

    def _shape_match(self, shape1, shape2):
        if shape1 == shape2:
            return True
        if len(shape1) == 1 and shape1[0] == math.prod(shape2):
            return True
        return False

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        return ArrayMaskFieldList(*args, **kwargs)

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, ArrayFieldListCore) for _ in sources):
            raise ValueError("ArrayFieldList can only be merged to another ArrayFieldLists")
        if not all(s.array_backend is s[0].array_backend for s in sources):
            raise ValueError("Only fieldlists with the same array backend can be merged")

        merger = ListMerger(sources)
        return merger.to_fieldlist()

    def __repr__(self):
        return f"{self.__class__.__name__}(fields={len(self)})"

    def _to_array_fieldlist(self, array_backend=None, **kwargs):
        if self[0]._array_matches(self._array[0], **kwargs):
            return self
        else:
            return type(self)(self.to_array(array_backend=array_backend, **kwargs), self._metadata)

    def save(self, filename, append=False, check_nans=True, bits_per_value=None):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str
            The target file path.
        append: bool
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists.
        check_nans: bool
            Replace nans in the values with GRIB missing values when generating the output.
        bits_per_value: int or None
            Set the ``bitsPerValue`` GRIB key in the generated output. When None the
            ``bitsPerValue`` stored in the metadata will be used.
        """
        super().save(
            filename,
            append=append,
            check_nans=check_nans,
            bits_per_value=bits_per_value,
        )


# class MultiUnwindMerger:
#     def __init__(self, sources):
#         self.sources = list(self._flatten(sources))

#     def _flatten(self, sources):
#         if isinstance(sources, ArrayMultiFieldList):
#             for s in sources.indexes:
#                 yield from self._flatten(s)
#         elif isinstance(sources, list):
#             for s in sources:
#                 yield from self._flatten(s)
#         else:
#             yield sources

#     def to_fieldlist(self):

#         return ArrayMultiFieldList(self.sources)


class ListMerger:
    def __init__(self, sources):
        self.sources = sources

    def to_fieldlist(self):
        array = []
        metadata = []
        for s in self.sources:
            for f in s:
                array.append(f._array)
                metadata.append(f._metadata)
        array_backend = None if len(self.sources) == 0 else self.sources[0].array_backend
        return ArrayFieldList(array, metadata, array_backend=array_backend)


class ArrayFieldList(ArrayFieldListCore):
    r"""Represent a list of :obj:`ArrayField <data.sources.array_list.ArrayField>`\ s.

    The preferred way to create a ArrayFieldList is to use either the
    static :obj:`from_array` method or the :obj:`to_fieldlist` method.

    See Also
    --------
    from_array
    to_fieldlist

    """

    def _getitem(self, n):
        if isinstance(n, int):
            return ArrayField(self._array[n], self._metadata[n], self.array_backend)

    def __len__(self):
        return len(self._array) if isinstance(self._array, list) else self._array.shape[0]


class ArrayMaskFieldList(ArrayFieldListCore, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_mask(self, self)


class ArrayMultiFieldList(ArrayFieldListCore, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_multi(self, self)
