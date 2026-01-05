Version 0.18 Updates
/////////////////////////


Version 0.18.4
===============

Dependencies
+++++++++++++++

- Disabled using ``netcdf4=1.7.4`` in the dependencies since it did not provide wheels for python 3.12 and 3.13 (:pr:`869`). See: https://github.com/Unidata/netcdf4-python/issues/1461


Version 0.18.3
===============

Fixes
++++++++

- Fixed issue when using the :ref:`data-sources-fdb` source with the ``lazy=True`` option resulted in string values instead of int for the following metadata keys: "level", "levelist", "date", "time", "step" (:pr:`858`).


Version 0.18.2
===============

Fixes
++++++++

- Fixed issue when the ``time_dim_mode="valid_time"`` option in :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` did not work correctly when converted a :ref:`data-sources-lod` FieldList to Xarray (:pr:`850`).



Version 0.18.1
===============

Fixes
++++++++

- Fixed issue when the ``valid_datetime`` was not correctly constructed for GRIB data containing sub-minute steps (:pr:`845`).


Version 0.18.0
===============

Request based sources
++++++++++++++++++++++++++++++

Unified the way requests are specified/parsed for request-based sources (:pr:`828`). Existing code still works without modification.

The new common interface looks like this:

.. code-block:: bash

    from_source(name, custom args ..., *args, request=None, custom kwargs ..., **kwargs)

with:

    - ``*args`` : tuple. Positional arguments representing request dictionaries. Each item can be dictionary or a list/tuple of dictionaries.
    - ``**kwargs`` : dict. Keyword arguments representing request parameters.
    - ``request`` : dict or list of dict. A single request dictionary or a list/tuple of request dictionaries.

The logic applied to build the requests is described :doc:`here </guide/misc/request_args>`.

This is implemented for the following sources: :ref:`data-sources-ads`, :ref:`data-sources-cds`, :ref:`data-sources-fdb`, :ref:`data-sources-mars`, :ref:`data-sources-eod`, :ref:`data-sources-polytope`, :ref:`data-sources-wekeo`, and :ref:`data-sources-wekeocds`.

The following exceptions apply:

    - :ref:`data-sources-polytope` passes all ``**kwargs`` to initialise the client
    - :ref:`data-sources-fdb` cannot handle multiple requests


New features
++++++++++++++++++++++++++++++

- Implemented caching for the :ref:`data-sources-polytope` source to speed up repeated retrievals of the same data (:pr:`827`).

Fixes
++++++++

- Fixed issue when the Field.clone method did not properly raise NotImplementedError (:pr:`832`)
