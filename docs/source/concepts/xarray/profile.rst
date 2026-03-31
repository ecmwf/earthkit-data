.. _xr_profile:

Xarray engine: profiles
-------------------------

:py:meth:`~earthkit.data.readers.grib.xarray.XarrayMixIn.to_xarray` has a large number of keyword arguments to control how the Xarray dataset is generated. To simplify the usage we can define **profiles** providing custom defaults for most of the keyword arguments. Profiles can be specified via the ``profile`` kwarg, which accepts the following values:

- :ref:`None <xr_profile_none>`: base profile which provides defaults for any other profile, including a custom profile defined via a dictionary (see below)
- :ref:`"earthkit" <xr_profile_earthkit>`: the **default** profile for the earthkit engine, which is used when no profile is specified
- :ref:`"mars" <xr_profile_mars>`: using some MARS specific GRIB metadata keys to generate the Xarray dataset
- :ref:`"grib" <xr_profile_grib>`: as "mars" but with some changes
- dictionary: a custom profile
