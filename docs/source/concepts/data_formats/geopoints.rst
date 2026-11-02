.. _geopoints:

Geopoints format
=================

`Geopoints <https://metview.readthedocs.io/en/latest/data_types/geopoints.html>`__ is the ASCII format
used by Metview to store spatially irregular data, e.g. observations. Each data point has a location
(latitude and longitude), a level, a date and time and the value of one or more parameters. When the
values of two parameters are stored they can be interpreted as the components of a vector quantity,
such as wind.

*earthkit-data* can read geopoints files with :ref:`from_source() <data-sources-file>` and convert
them into a Pandas DataFrame, an Xarray dataset, a featurelist or a fieldlist. This page describes the file format, and for each
variant of it the DataFrame that *earthkit-data* generates. The Metview documentation is the reference for
the format itself, and the :ref:`/tutorials/geopoints/geopoints.ipynb` notebook shows the examples
in action.

.. note::

    The format description follows the `Metview documentation
    <https://metview.readthedocs.io/en/latest/data_types/geopoints.html>`__. Metview-specific features
    such as the Macro/Python functions, plotting and operations on geopoints are not part of
    *earthkit-data* and are not covered here.


Reading geopoints in earthkit-data
-----------------------------------

A geopoints file is read like any other file:

.. code-block:: python

    import earthkit.data as ekd

    ds = ekd.from_source("file", "obs.gpt")
    df = ds.to_pandas()
    xr_ds = ds.to_xarray()

The resulting :ref:`data object <data-object>` is a
:py:class:`~earthkit.data.data.geopoints.GeopointsData`. The most important rules are:

- The file is recognised by its first line (``#GEO`` or ``#GEOPOINTSET``), whatever the file extension
  is. The only exception is a file name ending in ``.csv``, which is always read as a CSV file.
- :py:meth:`to_pandas` returns a DataFrame with one row per data point. The columns depend on the
  format of the file, see the sections below.
- Dates and times are combined into a single ``date`` column of datetime type. The time is
  expressed as HHMM, e.g. a time of ``1200`` is 12:00 while a time of ``12`` is interpreted as ``0012``,
  i.e. 00:12. In the formats with a date and a time there is no separate ``time`` column in the DataFrame.
  A date that cannot be interpreted becomes NaT. The :ref:`NCOLS format <geopoints-ncols>` has some
  special cases, which are described in its section.
- The numeric columns are floating point numbers, with the exception of the ``time`` column of an NCOLS
  file that has no date (see below), and ``stnid``, which is text. The geopoints missing value ``3e38``
  is converted into NaN, also in the latitude and longitude columns.
- In the standard and XYV formats the value column can contain text, which is kept as written. The other
  formats only accept numbers in their value columns.
- :py:meth:`to_xarray` returns the Dataset generated from the DataFrame, so it has the same variables,
  all of them defined along a single ``index`` dimension.


The geopoints file formats
---------------------------

A geopoints file is an ASCII file containing a header section and a data section made of several
columns. There are a few different flavours of the format, described below.

The data elements that can be present in a geopoints file are the point coordinates (latitude
and longitude), the level, the date, the time and the value of either one or two parameters.

The format does not care about the alignment of the columns, it just requires at least one whitespace
character between the entries. The following elements must be present:

- an initial line tagged with the keyword ``#GEO``
- a line tagged with the keyword ``#DATA``
- the data points themselves

There can also be an optional section for metadata, which must start with ``#METADATA``, see
:ref:`geopoints-metadata` below. The lines in-between the header and the data sections are for
human-readable information only and are not used in the interpretation of the file. All the formats
apart from the standard format require an additional line in the header to specify the format; this
line must start with ``#FORMAT`` followed by the name of the format being used.

A time is expressed as HHMM, so a time of 12 means 0012, i.e. 00:12.

In the data section each line holds one data point. Lines starting with ``#`` and very short lines
(at most four characters) are ignored.


Standard (6-column) geopoints
+++++++++++++++++++++++++++++

This is the default format, used when there is no ``#FORMAT`` line. The columns are the latitude, longitude,
level, date (YYYYMMDD), time (HHMM) and value. The following example shows a geopoints file containing dry
bulb temperature at 2m (PARAMETER = 12004).

.. code-block:: none

    #GEO
    PARAMETER = 12004
    lat        long    level  date       time    value
    #DATA
    36.15      -5.35     0   19970810    1200    300.9
    34.58      32.98     0   19970810    1200    301.6
    41.97      21.65     0   19970810    1200    299.4
    45.03       7.73     0   19970810    1200    294
    45.67       9.7      0   19970810    1200    302.2
    44.43       9.93     0   19970810    1200    293.4

The resulting DataFrame has the columns ``latitude``, ``longitude``, ``level``, ``date`` and ``value``.

The value column can also contain text instead of numbers (even mixed with numbers); the same applies to
the XYV format below. In the
DataFrame such a ``value`` column keeps every row as it is written in the file: numbers as numbers, text as text.


Format XYV (compact format)
+++++++++++++++++++++++++++

This format allows data to be specified with just three columns: X (longitude), Y (latitude) and V
(value). The start of an example file would look like the following:

.. code-block:: none

    #GEO
    #FORMAT XYV
    PARAMETER = 12004
    x/long y/lat value
    #DATA
    -5.35  36.15  300.9
    32.98  34.58  301.6
    21.65  41.97  299.4

The resulting DataFrame has the columns ``longitude``, ``latitude`` and ``value``. The format has no level or
date information, so there are no such columns.


Format XY_VECTOR (XY vector format)
+++++++++++++++++++++++++++++++++++

This format allows two parameters to be stored as the components of a two-dimensional vector (for example
the u and v components of the wind). The start of an example file would look like the following:

.. code-block:: none

    #GEO
    #FORMAT XY_VECTOR
    # lat    lon   height   date       time      u       v
    #DATA
    80       0      0      20030617    1200   -4.9001  -8.3126
    80       5.5    0      20030617    1200   -5.6628  -7.7252
    80       11     0      20030617    1200   -6.4254  -7.13829

The resulting DataFrame has the columns ``latitude``, ``longitude``, ``level``, ``date``, ``x-comp``
and ``y-comp``.


Format POLAR_VECTOR (polar vector format)
+++++++++++++++++++++++++++++++++++++++++

This format allows two parameters to be stored as the speed and direction of a two-dimensional vector,
the direction being specified in degrees where zero is due South and angles increase clockwise. The
start of an example file would look like the following:

.. code-block:: none

    #GEO
    #FORMAT POLAR_VECTOR
    # lat      lon     height     date       time   speed   direction
    #DATA
    50.97     6.05      0      20030614     1200     4       90
    41.97     21.65     0      20030614     1200     5       330
    35.85     14.48     0      20030614     1200     11      170

The resulting DataFrame has the columns ``latitude``, ``longitude``, ``level``, ``date``, ``magnitude``
and ``angle``.


.. _geopoints-ncols:

Format NCOLS (multi-column format)
++++++++++++++++++++++++++++++++++

This format allows any number of parameters to be stored in a geopoints file. The ``#COLUMNS`` section is
used to interpret the columns, as they can be put in any order: the line following ``#COLUMNS`` contains the
column names. The following column names are reserved and are treated specially (as coordinate columns):
``latitude``, ``longitude``, ``level``, ``elevation``, ``date``, ``time`` and ``stnid``. A column with a
different name is treated as a value column. The data must be all numeric, apart from ``stnid``, which is
stored as a string. The ``latitude`` and ``longitude`` columns are required and all the coordinate columns
must come before the first value column.

The start of an example file would look like the following:

.. code-block:: none

    #GEO
    #FORMAT NCOLS
    #COLUMNS
    latitude longitude  time date       t2     o3    td    rh
    #DATA
    32.55   35.85  0600    20120218    273.9   35   280.3   75
    31.72   35.98  1800    20120218    274.9   24   290.4   68
    51.93   8.32   1200    20140218    278.9   28   300.5   34
    41.1    20.82  1200    20150218    279.9   83   310.6   42

The columns of the resulting DataFrame are the ones listed in ``#COLUMNS``, in the same order. In the example
above they are ``stnid``, ``latitude``, ``longitude``, ``date``, ``t2``, ``o3``, ``td`` and ``rh``,
where ``stnid`` is added because the file has no such column (see below) and ``time`` is merged into
``date``. The special cases are:

- A ``stnid`` column is always present in the DataFrame. If ``stnid`` is listed in ``#COLUMNS`` it keeps its
  position from the file. If the file has no ``stnid`` column, one is added as the first column and it is
  filled with None. Station ids are kept as text (so e.g. ``007`` stays ``"007"``), a ``?``
  means a missing id (None), and the escape sequences ``\32\`` and ``\9\`` stand for a space and a tab,
  respectively.
- ``time`` is merged into ``date`` when the file has a ``date`` column. If there is a ``date`` but no
  ``time`` column, the time is midnight. If there is a ``time`` but no ``date`` column, ``time`` stays
  in the DataFrame as a column, normally of integer type (float when it has missing values).
- When there is no ``#COLUMNS`` section, the columns are assumed to be ``stnid``, ``latitude``, ``longitude``,
  ``level``, ``date``, ``time`` and ``elevation`` (in this order, followed by the value columns), with ``time``
  merged into ``date`` as usual.
- When the data has more value columns than are named in ``#COLUMNS``, the extra ones are called ``_v1``,
  ``_v2``, etc. So a file with the header ``stnid latitude time longitude level date`` and three value columns
  per row results in the DataFrame columns ``stnid``, ``latitude``, ``longitude``, ``level``, ``date``,
  ``_v1``, ``_v2`` and ``_v3``.


.. _geopoints-metadata:

Storing metadata
----------------

A geopoints file can have a section of metadata key-value pairs in its header, before the ``#DATA`` line,
as illustrated here:

.. code-block:: none

    #GEO
    PARAMETER = 12030
    #METADATA
    param=temperature
    date=20130804
    time=1200
    level=0.2
    #lat    long    level   date    time    value
    #DATA
    55.01   8.41    0.2     20130804  1200  294.4
    54.33   8.60    0.2     20130804  1200  296.9

Here, four pieces of metadata are stored. Each ``key=value`` line is a separate item and the section runs
until the ``#DATA`` line (or a ``#DB_INFO`` section, see below).

The metadata does not appear in the DataFrame. It is available from the features of the featurelist
generated with ``to_featurelist()``, see :ref:`geopoints-featurelist` below. It is also stored in the labels of
the fields generated with ``to_fieldlist()``, see :ref:`geopoints-fieldlist`.


.. _geopoints-featurelist:

Metadata in a featurelist
+++++++++++++++++++++++++

:py:meth:`to_featurelist` converts the data into a featurelist, whose features give access to the metadata:

- By default (``mode="block"``) there is one feature per geopoints block, so a geopoints file gives one
  feature and a :ref:`geopointset <geopoints-geopointset>` gives one feature per block. The
  ``metadata()`` of a feature is a dict with the ``key=value`` pairs of the ``#METADATA`` section of its block,
  and nothing else. Values that are integers or floats are converted to numbers, the others are kept as
  text. A block without ``#METADATA`` has empty metadata. For the example above:

  .. code-block:: python

      fl = ekd.from_source("file", "metadata.gpt").to_featurelist()
      fl[0].metadata()
      # {'param': 'temperature', 'date': 20130804, 'time': 1200, 'level': 0.2}

- With ``mode="row"`` there is one feature per data point. The ``metadata()`` of a feature is the
  ``#METADATA`` of its block plus the values of the columns of the row (as in the DataFrame, e.g.
  ``latitude``, ``longitude``, ``level``, ``date`` and ``value``). If a name is in both, the value of the
  row is used.

The featurelist can be indexed and sliced, and it has ``sel()``, ``order_by()`` and ``ls()``. See the
:ref:`/tutorials/geopoints/geopoints.ipynb` notebook for examples.


.. _geopoints-fieldlist:

Geopoints as a fieldlist
++++++++++++++++++++++++

:py:meth:`to_fieldlist` converts the data into a fieldlist of point fields, so the data can be used with the
field API (``sel()``, ``order_by()``, ``ls()``, ``get()``, ...). The geography of a field is a list of
points: ``geography.latlons()`` returns the latitudes and longitudes as arrays of shape ``(n,)``.

.. code-block:: python

    fl = ekd.from_source("file", "metadata.gpt").to_fieldlist()
    fl[0].values
    fl[0].geography.latlons()

The fields are built as follows:

- **Value columns.** There is one field per value column. These are ``value`` in the standard and XYV formats,
  ``x-comp`` and ``y-comp`` in XY_VECTOR, ``magnitude`` and ``angle`` in POLAR_VECTOR, and all the columns
  that are not coordinate columns in NCOLS. A value column with text is skipped with a warning. A block
  without data points gives no field. ``stnid`` and ``elevation`` are not stored in the fields (but see
  ``group_by`` below).
- **Time.** The date and time of the row is the valid time of the field (``time.valid_datetime``). If the
  ``#METADATA`` has a ``step`` (a number of hours or text such as ``6h``) the base time is the valid time minus
  the step, otherwise the step is 0. A block without a ``date`` column, e.g. XYV, uses the ``date`` and ``time``
  of the ``#METADATA`` if present, otherwise the field has no time.
- **Level.** The level is the value of the ``level`` column, or the ``level`` of the ``#METADATA`` if there is no
  such column. The ``levtype`` of the ``#METADATA`` (e.g. ``pl``, ``sfc``, ``ml``) sets the level type
  (``vertical.level_type``).
- **Parameter.** If the block has a single value column, ``parameter.variable`` is the ``param`` (or ``shortName``)
  of the ``#METADATA`` when present, otherwise the column name (e.g. ``value``). With several value columns it is
  the column name. The ``units`` of the ``#METADATA`` sets ``parameter.units``.
- **Labels.** All the ``key=value`` pairs of the ``#METADATA`` are stored in the labels of the field, e.g.
  ``f.get("labels.param")``. See :ref:`labels_component` for details on labels.

The ``mode`` option controls how the data is split into fields:

- ``mode="block"`` (the default) gives one field per block (and value column). The time and the level are taken from the
  **first row** of the block; no warning is given when the other rows have different values.
- ``mode="group"`` splits each block into groups of rows with the same ``date`` and ``level`` columns and gives
  one field per group (and value column), in the order the groups first appear in the block. The time and level of a field
  are taken from its group. ``group_by`` replaces these columns by a list of other columns of the data, e.g.
  ``to_fieldlist(mode="group", group_by=["stnid"])`` gives one field per station. The values of the group columns
  other than ``date`` and ``level`` are stored in the labels. If a block has no grouping columns it is a
  single group. ``group_by`` cannot be used with ``mode="block"``.

The following limits apply:

- The fields cannot be encoded to GRIB, because the points are not on a grid.
- ``to_numpy()`` of the fieldlist needs the same number of points in all fields, but not the same coordinates.
  The ``to_numpy()`` of a single field always works.
- ``to_xarray()`` of the fieldlist needs all fields to share the same set of points; otherwise it fails with
  "Fields do not have the same grid geometry".
- The fields cannot be pickled or deep-copied.

See the :ref:`/tutorials/geopoints/geopoints.ipynb` notebook for examples.


Storing data origin information
-------------------------------

The details of the origin of the data can also be stored in the file in a ``#DB_INFO`` section. The following
example shows the information generated by an ODB query:

.. code-block:: none

    #GEO
    lat long level date time value
    #DB_INFO
    DB_SYSTEM: ODB
    DB_COLUMN: lldegrees(lat@hdr);lldegrees(lon@hdr); ; ; ;obsvalue@body
    DB_COLUMN_ALIAS: lldegrees(lat);lldegrees(lon); ; ; ;obsvalue@body
    DB_PATH: /tmp/cgi/odb/ECMA.conv
    DB_QUERY_BEGIN select lldegrees(lat), lldegrees(lon), obsvalue from hdr, body where varno=$t2m and obsvalue is not null
    DB_QUERY_END
    #DATA
    36.150 -5.350 0.000 0 0000 295.10000000

This section is generated automatically. *earthkit-data* skips it when reading the data.


Missing values
--------------

In a geopoints file the missing value is ``3e38`` (any spelling that represents this number, e.g. ``3e+38``,
is accepted). It can appear in the value columns and in the latitude and longitude columns as well. When the
data is converted with :py:meth:`to_pandas` or :py:meth:`to_xarray` all the missing values become NaN.

.. code-block:: none

    #GEO
    lat long level date time value
    #DATA
    45.03   7.73  0  20100810  1200  294.8
    45.67   9.7   0  20100810  1200  3e+38
    3e+38   8.11  0  20100810  1200  300.3

.. code-block:: python

    import earthkit.data as ekd

    df = ekd.from_source("file", "missing.gpt").to_pandas()
    print(df)

.. code-block:: none

       latitude  longitude  level                date  value
    0     45.03       7.73    0.0 2010-08-10 12:00:00  294.8
    1     45.67       9.70    0.0 2010-08-10 12:00:00    NaN
    2       NaN       8.11    0.0 2010-08-10 12:00:00  300.3


.. _geopoints-geopointset:

Geopointset file format
-----------------------

A geopointset is a collection of geopoints, used by Metview to group a set of observations into a single
entity. In a file it is simply a header followed by a concatenation of geopoints (each with its own ``#GEO``
line, header and data section). The overall header is this line:

.. code-block:: none

    #GEOPOINTSET

Here is an example with three geopoints inside the set. The second one has a metadata section:

.. code-block:: none

    #GEOPOINTSET
    #GEO
    # lat   lon height  date        time    value
    # Missing values represented by 3e+38 (not user-changeable)
    #DATA
    69.6523    18.9057 0   20130512    0   100869.8625
    63.4882    10.8795 0   20130512    0   100282.3392
    63.5657    10.694  0   20130512    0   100241.1666
    61.2928    5.0443  0   20130512    0   99852.18932
    #GEO
    # lat   lon height  date        time    value
    # Missing values represented by 3e+38 (not user-changeable)
    #METADATA
    param=geopotential
    #DATA
    60.82  23.5    0   20130512    600 101045.8
    #GEO
    # lat   lon height  date        time    value
    # Missing values represented by 3e+38 (not user-changeable)
    #DATA
    55.01  8.41    0   20130513    0   100949.1809
    54.33  8.62    0   20130513    0   101027.9101
    53.71  7.15    0   20130513    0   100846.619

Each geopoints block is self-contained: it has its own format, columns and metadata.

When a geopointset file is read with *earthkit-data*, :py:meth:`to_pandas` stacks the data of all the
blocks into a single DataFrame with a continuous index. If the blocks do not have the same columns, the
columns missing from a block are filled with NaN. For the file above the result is:

.. code-block:: none

       latitude  longitude  level                date         value
    0   69.6523    18.9057    0.0 2013-05-12 00:00:00  100869.86250
    1   63.4882    10.8795    0.0 2013-05-12 00:00:00  100282.33920
    2   63.5657    10.6940    0.0 2013-05-12 00:00:00  100241.16660
    3   61.2928     5.0443    0.0 2013-05-12 00:00:00   99852.18932
    4   60.8200    23.5000    0.0 2013-05-12 06:00:00  101045.80000
    5   55.0100     8.4100    0.0 2013-05-13 00:00:00  100949.18090
    6   54.3300     8.6200    0.0 2013-05-13 00:00:00  101027.91010
    7   53.7100     7.1500    0.0 2013-05-13 00:00:00  100846.61900

The same applies when several geopoints files are read at once (a list of files, a glob pattern or a directory):
the result is a single data object, :py:meth:`to_pandas` stacks the data of all the files, and the featurelist
contains the features of all the files in order.


Examples
--------

    - :ref:`/tutorials/geopoints/geopoints.ipynb`

See also
--------

    - `Geopoints in the Metview documentation <https://metview.readthedocs.io/en/latest/data_types/geopoints.html>`__
    - `Geopointsets in the Metview documentation <https://metview.readthedocs.io/en/latest/metview/macro/data_types/geopointset.html>`__
