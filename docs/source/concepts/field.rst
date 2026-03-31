Field and FieldList
=======================

Field
--------
The :py:class:`~earthkit.data.core.field.Field` class represents a horizontal slice of the atmosphere/hydrosphere at a given time.

A field is a fundamental data structure in EarthKit Data, and it contains both metadata and data values.

The Field class is not polymorphic, but is a composition of polymorphic components. Each component is designed to handle a specific aspect of the field's metadata, such as time, level, or spatial information. This design allows for greater flexibility and modularity in handling different types of data and metadata.

Fields are typically created as part of a :py:class:`~earthkit.data.core.fieldlist.FieldList` when reading data from a source, and they can be accessed and manipulated through the FieldList's methods.


FieldList
------------
A :py:class:`~earthkit.data.core.fieldlist.FieldList` is a collection of :py:class:`~earthkit.data.core.field.Field` objects. It provides methods to access and manipulate the fields it contains, such as selecting fields based on metadata values, extracting data values and converting the fieldlists to other formats (e.g., Xarray datasets).


How-tos:

    - :ref:`/how-tos/field/field_overview.ipynb`
    - :ref:`/how-tos/grib/grib_overview.ipynb``
