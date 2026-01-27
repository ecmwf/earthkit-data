# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.indexing.simple import SimpleFieldListCore

GRIB_KEYS_NAMES = [
    "class",
    "stream",
    "levtype",
    "type",
    "expver",
    "date",
    "hdate",
    "andate",
    "time",
    "antime",
    "reference",
    "anoffset",
    "verify",
    "fcmonth",
    "fcperiod",
    "leadtime",
    "opttime",
    "origin",
    "domain",
    "method",
    "diagnostic",
    "iteration",
    "number",
    "quantile",
    "levelist",
    "param",
]

LS_KEYS = [
    "name",
    "level",
    "level_type",
    "base_datetime",
    "step",
    "valid_datetime",
    "number",
    "gridType",
]
INDEX_KEYS = list(GRIB_KEYS_NAMES)

DESCRIBE_KEYS = [
    "shortName",
    "typeOfLevel",
    "level",
    "date",
    "time",
    "stepRange",
    "number",
    "paramId",
    "marsClass",
    "marsStream",
    "marsType",
    "experimentVersionNumber",
]


class FieldList(SimpleFieldListCore):
    def __init__(self):
        r"""Initialize a FieldList object."""
        self.__fields = []

    @property
    def _fields(self):
        return self.__fields

    @staticmethod
    def from_fields(fields):
        r"""Create a :class:`SimpleFieldList`.

        Parameters
        ----------
        fields: iterable
            Iterable of :obj:`Field` objects.

        Returns
        -------
        :class:`SimpleFieldList`

        """
        from earthkit.data.indexing.simple import SimpleFieldList

        return SimpleFieldList.from_fields(fields)

    @staticmethod
    def from_numpy(array, metadata):
        raise NotImplementedError("SimpleFieldList.from_numpy is not implemented")

    @staticmethod
    def from_array(array, metadata):
        raise NotImplementedError("SimpleFieldList.from_array is not implemented")

    @classmethod
    def merge(cls, sources):
        raise ValueError("Cannot merge empty FieldLists")

    def ignore(self):
        # Used by multi-source
        return True

    def __and__(self, other):
        return other

    def append(self, other):
        from earthkit.data.indexing.simple import SimpleFieldList

        return SimpleFieldList([other])

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs._fields[i] for i in indices])


# class FieldList(FieldListCore):
#     @staticmethod
#     def from_fields(fields):
#         r"""Create a :class:`SimpleFieldList`.

#         Parameters
#         ----------
#         fields: iterable
#             Iterable of :obj:`Field` objects.

#         Returns
#         -------
#         :class:`SimpleFieldList`

#         """
#         from earthkit.data.indexing.simple import SimpleFieldList

#         return SimpleFieldList.from_fields(fields)

#     @staticmethod
#     def from_numpy(array, metadata):
#         raise NotImplementedError("FieldList.from_numpy is not implemented")

#     @staticmethod
#     def from_array(array, metadata):
#         raise NotImplementedError("FieldList.from_array is not implemented")

#     def __len__(self):
#         return 0

#     def __getitem__(self, n):
#         raise IndexError("Empty FieldList has no elements")

#     @property
#     def values(self):
#         raise ValueError("Empty FieldList has no values")

#     def to_numpy(self, **kwargs):
#         raise ValueError("Empty FieldList has no values")

#     def to_array(self, **kwargs):
#         raise ValueError("Empty FieldList has no values")

#     def data(
#         self,
#         keys=("lat", "lon", "value"),
#         flatten=False,
#         dtype=None,
#         index=None,
#     ):
#         raise ValueError("Empty FieldList has no values")

#     def datetime(self):
#         raise ValueError("Empty FieldList has no values")

#     @property
#     def geography(self):
#         raise ValueError("Empty FieldList has no values")

#     def to_latlon(self, index=None, **kwargs):
#         raise ValueError("EmptyFieldList has no values")

#     def to_points(self, **kwargs):
#         raise ValueError("EmptyFieldList has no values")

#     def bounding_box(self):
#         pass

#     def projection(self):
#         pass

#     def get(self, *keys, remapping=None, patches=None, **kwargs):
#         return []

#     def get_as_dict(self, *args, group=False, remapping=None, patches=None, **kwargs):
#         return []

#     def metadata(self, *args, **kwargs):
#         return []

#     def indices(self, squeeze=False):
#         return {}

#     def index(self, key):
#         return []

#     def ls(self, n=None, keys=None, extra_keys=None, namespace=None):
#         return []

#     def head(self, n=5, **kwargs):
#         return []

#     def tail(self, n=5, **kwargs):
#         return []

#     def describe(self, *args, **kwargs):
#         return []

#     def to_fieldlist(self, array_backend=None, array_namespace=None, device=None, **kwargs):
#         return self

#     def to_tensor(self, *args, **kwargs):
#         pass

#     def cube(self, *args, **kwargs):
#         pass

#     def default_encoder(self):
#         pass

#     def _encode(self, encoder, **kwargs):
#         """Double dispatch to the encoder"""
#         pass

#     def normalise_key_values(self, **kwargs):
#         pass

#     @classmethod
#     def merge(cls, sources):
#         raise ValueError("Cannot merge empty FieldLists")

#     def __and__(self, other):
#         return other

#     def append(self, other):
#         from earthkit.data.indexing.simple import SimpleFieldList

#         return SimpleFieldList([other])
