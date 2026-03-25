.. _xr_profile:

Xarray engine: profiles
-------------------------

:py:meth:`~data.readers.grib.xarray.XarrayMixIn.to_xarray` has a large number of keyword arguments to control how the Xarray dataset is generated. To simplify the usage we can define **profiles** providing custom defaults for most of the keyword arguments. Profiles can be specified via the ``profile`` kwarg, which accepts the following values:

- :ref:`None <xr_profile_none>`: no profile is used
- :ref:`"mars" <xr_profile_mars>`: the **default** profile
- :ref:`"grib" <xr_profile_grib>`: as "mars" but with some changes
- dictionary: a custom profile
