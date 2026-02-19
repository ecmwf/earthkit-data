# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.indexing.simple import SimpleFieldListCore


class EmptyFieldList(SimpleFieldListCore):
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

    @classmethod
    def merge(cls, sources):
        sources = [s for s in sources if not s.ignore()]
        if len(sources) > 1:
            return sources[0].merge(sources[1:])
        elif len(sources) == 1:
            return sources[0]
        raise ValueError("No sources to merge")

    def ignore(self):
        # Used by multi-source
        return True

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        raise ValueError("Cannot create a mask index from an empty FieldList")
        # assert len(args) == 2
        # fs = args[0]
        # indices = list(args[1])
        # return cls.from_fields([fs._fields[i] for i in indices])

    def mutate_source(self):
        return self

    def mutate(self):
        return self
