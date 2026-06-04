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
    - :ref:`/how-tos/grib/grib_overview.ipynb`

Immutability of field values
------------------------------

The values of a field are immutable, meaning that they cannot be modified in place. When you access the values of a field, you will receive a copy of the data, and any modifications to that copy will not affect the original field's data. This design choice ensures that the integrity of the field's data is maintained and prevents unintended side effects when working with field values.

Arithmetic operations on fields
------------------------------
Arithmetic operations on fields (e.g., addition, subtraction, multiplication, division) are directly supported, and they return new field objects with the result of the operation. When performing arithmetic operations, the metadata of the resulting field is derived from first operand without any
alterations.
