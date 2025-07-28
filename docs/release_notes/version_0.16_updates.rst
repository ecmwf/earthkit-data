Version 0.16 Updates
/////////////////////////


Version 0.16.0
===============

Xarray engine
++++++++++++++++++++++++++++++

- Implemented mono variable (single dataarray containing all the parameters from a GRIB fieldlist) in Xarray engine (:pr:`734`). See the notebook example :ref:`/examples/xarray_engine_mono_variable.ipynb`
- Allowed specifying metadata defaults for :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray` (:pr:`738`) via the ``fill`` option.See the notebook example :ref:`/examples/xarray_engine_mono_variable.ipynb`
- Improved the Xarray support in the encoders (:pr:`750`).


Experimental features
------------------------------

- Added GPU support for the Xarray engine (:pr:`745`). See the notebook example :ref:`/examples/xarray_cupy.ipynb`
- Added ``grid_spec`` property to Xarray earthkit accessor (:pr:`751`).
