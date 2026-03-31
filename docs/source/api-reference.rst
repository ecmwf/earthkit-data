API Reference Guide
===================

Top level API functions and objects
-----------------------------------------

These functions/objects can be imported directly from the top level package and are the main entry points to work with data in `earthkit-data`.


.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Function/Object
     - Description
   * - :func:`from_source`
     - Read data from a given source and return a :ref:`data object <data-object>`.
   * - :func:`from_object`
     - Read data from a given object and return a :ref:`data object <data-object>`.
   * - :func:`to_target`
     - Write data to a given target.
   * - :func:`~earthkit.data.core.fieldlist.create_fieldlist`
     - Create a fieldlist object.
   * - :func:`create_target`
     - Create a target object.
   * - :func:`create_encoder`
     - Create an encoder object.
   * - :func:`~earthkit.data.utils.concat.concat`
     - Concatenate multiple data objects into a single one.
   * - :py:class:`cache <earthkit.data.core.caching.CACHE>`
     - A global cache object. See: :ref:`caching` for more details.
   * - :py:class:`config <earthkit.data.core.config.CONFIG>`
     - A config object that can be used to set global configuration options for earthkit-data. See: :ref:`config` for more details.


Top level API classes
-------------------------

.. list-table:: Top level API classes
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Description
   * - :py:class:`~earthkit.data.core.field.Field`
     - A horizontal slice of the atmosphere/hydrosphere at a given time.
   * - :py:class:`~earthkit.data.core.fieldlist.FieldList`
     - A collection of fields.



The full API reference guide
-------------------------------

Traverse through the API reference guide to find out more about the available functions
and classes in `earthkit-data`.

- :doc:`autoapi/earthkit/data/index`.
