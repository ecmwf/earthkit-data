.. _grib_encoder:

GRIB encoder
============

:py:class:`~earthkit.data.encoders.grib.GribEncoder` encodes data into GRIB messages.
It is selected automatically when writing to a file with a ``.grib``, ``.grb``,
``.grib1``, ``.grib2``, ``.grb1``, or ``.grb2`` extension, or explicitly by passing
``encoder="grib"`` to :func:`~earthkit.data.to_target`.


Constructing a GribEncoder
--------------------------

.. code-block:: python

    from earthkit.data import create_encoder

    # No preset — template and metadata supplied per encode() call
    enc = create_encoder("grib")

    # Preset template and metadata applied to every encode() call
    enc = create_encoder("grib", template=field, shortName="2t")

.. list-table:: Constructor parameters
   :header-rows: 1
   :widths: 22 78

   * - Parameter
     - Description
   * - ``template``
     - Default template used as the basis for every encoded message. Accepts a
       :py:class:`~earthkit.data.core.field.Field`, a ``GribCodesHandle``, a raw GRIB
       message as ``bytes``, an ecCodes GRIB sample name as a ``str``, or a raw ecCodes
       handle as an ``int``. See :ref:`grib_encoder_templates` for details.
   * - ``metadata``
     - Dictionary of default ecCodes GRIB keys applied to every message. Keys may
       optionally be prefixed with ``"metadata."`` and format-independent dotted keys
       (e.g. ``"parameter.shortName"``) are also accepted. Per-call metadata passed to
       :meth:`encode` is merged on top, with per-call values taking precedence.
   * - ``**kwargs``
     - Additional keyword arguments treated as metadata keys, merged into ``metadata``.


.. _grib_encoder_encode:

The encode() method
-------------------

.. py:method:: GribEncoder.encode(data=None, values=None, metadata={}, template=None, check_nans=True, missing_value=9999, target=None, **kwargs)

   Encode one or more GRIB messages.

   :param data: Source data. Accepted types: :py:class:`~earthkit.data.core.field.Field`,
       :py:class:`~earthkit.data.core.fieldlist.FieldList`, NumPy array, or xarray
       Dataset/DataArray. Cannot be combined with both ``values`` and ``template``
       simultaneously.
   :param numpy.ndarray values: Raw values array. Takes precedence over any values carried
       by ``data`` or ``template`` when provided. If the array contains ``NaN`` values
       they are replaced with ``missing_value`` when ``check_nans=True``.
   :param dict metadata: Per-call metadata merged on top of the encoder's preset metadata.
       Accepts ecCodes GRIB keys, keys prefixed with ``"metadata."``, and format-independent
       dotted keys such as ``"parameter.shortName"``.
   :param template: Per-call template overriding the encoder's preset template. Accepted
       types are the same as for the constructor. Takes precedence over ``data`` when
       forming the GRIB handle, but values are still taken from ``data`` unless ``values``
       is also provided. Cannot be combined with both ``data`` and ``values``.
   :param bool check_nans: When ``True`` (default), ``NaN`` values in ``values`` are
       replaced with ``missing_value`` and ``bitmapPresent`` is set in the encoded message.
   :param float missing_value: Replacement value for ``NaN`` entries. Default is ``9999``.
   :param target: Target object passed through from :func:`~earthkit.data.to_target`. Some
       encoders use this to choose a more efficient output path (e.g. bypassing
       re-encoding when writing an unchanged GRIB file to disk).
   :param kwargs: Additional metadata keys, merged with ``metadata``.
   :returns: A :py:class:`~earthkit.data.encoders.grib.GribEncodedData` instance when a
       single message is produced, or a *generator* of
       :py:class:`~earthkit.data.encoders.grib.GribEncodedData` objects when encoding a
       FieldList or xarray Dataset.


Combining data, values, and template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``data``, ``values``, and ``template`` cannot all be specified at once. When two of
them are provided together the following rules apply:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Combination
     - Behaviour
   * - ``data`` + ``values``
     - Template comes from ``data``; values are taken from ``values``.
   * - ``data`` + ``template``
     - The GRIB handle comes from ``template``; values are taken from ``data``.
   * - ``values`` + ``template``
     - The GRIB handle comes from ``template``; values are taken from ``values``.


Encoding from values and metadata only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When neither ``data`` nor ``template`` is supplied, a new GRIB handle is constructed
entirely from ``values`` and ``metadata``. This is an experimental path and only
supports:

- **Regular lat/lon grids** — inferred from a 2-D ``values`` shape ``(Nj, Ni)``.
- **Reduced Gaussian grids** — inferred from a 1-D ``values`` shape matching a known
  Gaussian grid size.

Compulsory metadata keys (such as ``shortName`` or ``param``) must be present in
``metadata`` or the encoder's preset; a :exc:`ValueError` is raised if any are missing.


.. _grib_encoder_templates:

Templates
---------

A *template* is the GRIB message used as the structural basis for a new encoded
message. The encoder copies the template handle and then applies new values and
metadata on top.

Accepted template types:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Type
     - Description
   * - :py:class:`~earthkit.data.core.field.Field`
     - Any earthkit-data Field object. Its GRIB handle is cloned as the starting point.
   * - ``GribCodesHandle``
     - An earthkit-data internal GRIB handle wrapper.
   * - ``bytes``
     - A raw GRIB message buffer. Parsed into a handle via ecCodes.
   * - ``str``
     - The name of an ecCodes GRIB sample (e.g. ``"regular_ll_sfc_grib2"``).
   * - ``int``
     - A raw ecCodes handle integer, e.g. obtained from a low-level ecCodes call.
   * - ``None``
     - No template. A handle is constructed from ``data``, ``values``, and ``metadata``.


Metadata keys
-------------

All three sources of metadata (constructor preset, ``metadata`` argument, and
``**kwargs``) are merged together before encoding, with later sources winning:

1. Encoder preset (set at construction time).
2. ``metadata`` dict passed to :meth:`encode`.
3. ``**kwargs`` passed to :meth:`encode`.

Keys are accepted in three formats:

- **Plain ecCodes keys** — e.g. ``shortName="2t"``, ``step=6``, ``edition=2``.
- **``"metadata."``-prefixed keys** — e.g. ``"metadata.shortName"``; the prefix is
  stripped before the key is applied.
- **Format-independent dotted keys** — e.g. ``"parameter.shortName"``; these are
  applied first to produce a base handle, then any plain ecCodes keys are applied on top.


NaN handling
------------

When ``check_nans=True`` (the default), the encoder scans ``values`` for ``NaN`` entries.
If any are found:

- ``NaN`` values are replaced with ``missing_value`` (default ``9999``).
- ``bitmapPresent = 1`` and ``missingValue = missing_value`` are set on the encoded
  message automatically.


Usage examples
--------------

Encode with a preset template and override a metadata key:

.. code-block:: python

    import earthkit.data as ekd
    from earthkit.data import create_encoder

    template = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
    encoder = create_encoder("grib", template=template, shortName="msl")

    result = encoder.encode(values=template.values + 1.0, step=6)
    field = result.to_field()
    field.get("parameter.shortName")  # "msl"
    field.get("step")                 # 6

Encode without a preset template (template supplied per call):

.. code-block:: python

    encoder = create_encoder("grib")
    result = encoder.encode(
        values=template.values + 1.0,
        template=template,
        metadata={"shortName": "msl"},
        step=6,
    )

Encode an entire FieldList and write to a file:

.. code-block:: python

    import earthkit.data as ekd

    fs = ekd.from_source("sample", "test.grib").to_fieldlist()
    ekd.to_target("file", "out.grib", data=fs, encoder="grib")

Encode a FieldList using the encoder directly and iterate over results:

.. code-block:: python

    encoder = create_encoder("grib", template=template)
    for result in encoder.encode(data=fs):
        # result is a GribEncodedData for one field
        result.to_file(open("out.grib", "ab"))


How-tos
-------

- :ref:`/tutorials/target/grib_encoder.ipynb`
- :ref:`/tutorials/grib/grib_modify_metadata.ipynb`
- :ref:`/tutorials/grib/grib_modify_values.ipynb`
