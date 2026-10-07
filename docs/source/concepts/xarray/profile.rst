.. _xr_profile:

Xarray engine: profiles
-------------------------

:py:meth:`~earthkit.data.readers.grib.xarray.XarrayMixIn.to_xarray` has a large number of keyword arguments to control how the Xarray dataset is generated. To simplify the usage we can define **profiles** providing custom defaults for most of the keyword arguments. Profiles can be specified via the ``profile`` kwarg, which accepts the following values:

- :ref:`None <xr_profile_none>`: base profile which provides defaults for any other profile, including a custom profile defined via a dictionary (see below)
- :ref:`"earthkit" <xr_profile_earthkit>`: the **default** profile for the earthkit engine, which is used when no profile is specified
- :ref:`"mars" <xr_profile_mars>`: using some MARS specific GRIB metadata keys to generate the Xarray dataset
- :ref:`"grib" <xr_profile_grib>`: as "mars" but with some changes
- ``"defaults"``: the base profile (equivalent to ``None``)
- a path to a YAML or JSON file containing a custom profile
- dictionary: a custom profile
- a **list** of any of the above (except ``None``): the profiles are layered in order, each one overriding the options defined by the previous ones

Layering multiple profiles
++++++++++++++++++++++++++++

When ``profile`` is a list, the profiles are applied one after the other on top of the base defaults, so that each item overrides the options already set by the previous ones. This makes it easy to start from a pre-defined profile and refine it with a custom file or dictionary:

.. code-block:: python

    import earthkit.data

    fs = earthkit.data.from_source("sample", "pl.grib")

    # start from the "earthkit" profile and override some options from a custom file
    ds = fs.to_xarray(profile=["earthkit", "my_profile.yaml"])

    # a custom YAML/JSON file can also be used on its own
    ds = fs.to_xarray(profile="my_profile.yaml")

    # the same layering is available on the command line
    # (repeat --profile to layer them in order):
    #
    #   earthkit convert in.grib out.nc --profile earthkit --profile my_profile.yaml

A profile file is a YAML (``.yaml``/``.yml``) or JSON (``.json``) file containing a mapping of the same options accepted as ``to_xarray`` keyword arguments, e.g.:

.. code-block:: yaml

    # my_profile.yaml
    rename_variables:
      t: temperature
    add_valid_time_coord: true
