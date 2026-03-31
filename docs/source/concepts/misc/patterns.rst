.. _patterns:

Using patterns for the file-pattern source
==========================================

The :ref:`data-sources-file-pattern` source works with an input path pattern. The pattern is a string containing parameters within ``{}`` brackets. The way these parameters are substituted depends on the ``hive_partitioning`` option.

Pattern substitution
+++++++++++++++++++++

hive_partioning=False
/////////////////////////////

When ``hive_partioning=False`` we have to specify all the possible values for all the parameters. E.g.:

.. code-block:: python

    from_source(
        "file-pattern",
        "mydir/{year}/myfile_{param}.grib",
        year=[2023, 2024],
        param=["t", "r"],
    )

When this code is executed the file paths are constructed from the Cartesian product of the substituted values. The example above will result in a :py:class:`Fieldlist` built from the following paths::

    mydir/2023/myfile_t.grib
    mydir/2023/myfile_r.grib
    mydir/2024/myfile_t.grib
    mydir/2024/myfile_r.grib


hive_partioning=True
/////////////////////////////

When ``hive_partitioning=True`` the behaviour is different. The pattern values still can be specified, but is is optional since they can be determined dynamically. See :ref:`here <data-sources-file-pattern>` for details.

Pattern item types
++++++++++++++++++++

Each pattern parameter can have an optional type specifier.

The following pattern types are available:

- ``int``: enforce the input values to be integers. An optional format can be specified.

    .. code-block:: python

        {name: int}
        {name: int(format)}

    .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value/Error
        * - {step:int}
          - 5
          - "5"
        * - {step:int(%04d)}
          - 5
          - "0005"
        * - {step:int}
          - "5"
          - ValueError
        * - {step:int}
          - 5.0
          - ValueError

- ``float``: enforce the input values to be floats or ints. An optional format can be specified, the default is ``%g``.

    .. code-block:: python

        {name: float}
        {name: float(format)}

    .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value/Error
        * - {val:float}
          - 5.1
          - "5.1"
        * - {val:float}
          - 5.0
          - "5"
        * - {val:float}
          - 5
          - "5"
        * - {val:float(%.2f)}
          - 5.1
          - "5.10"
        * - {step:float}
          - "5.0"
          - ValueError

- ``enum``: enforce the input values to be one of the specified values

    .. code-block:: python

        {name: enum(value1, value2, value3)}


    .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value/Error
        * - {step:enum(0,6,12)}
          - [0, 6]
          - "0" and "6"
        * - {step:enum(0,6,12)}
          - [0,18]
          - ValueError

- ``date``: all values are cast to a datetime formatted with the ``datetime.strftime`` syntax. The formatting must be specified.

    .. code-block:: python

        {my_date: date(format)}

    .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value/Error
        * - {my_date:date(%Y-%m-%d)}
          - [datetime.datetime(2023, 1, 1), datetime.datetime(2023, 1, 2)]
          - "2023-01-01" and "2023-01-02"
        * - {my_date:date(%Y-%m-%d)}
          - ["20230101", "20230102"]
          - "2023-01-01" and "2023-01-02"

- ``strftime``: alias to ``date``

- ``strftimedelta``: all values are cast to a datetime by applying the specified timedelta. Datetime formatting must be specified.

    .. code-block:: python

        {my_date: strftimedelta(delta, format)}

    where ``delta`` can be specified in seconds, minutes, hours (the default is hours), e.g.::

        6
        -6h
        60m
        7200s

    .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value/Error
        * - {my_date:strftimedelta(-6,%Y-%m-%d_%H)}
          - [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 11, 6) ]
          - "2020-05-10_18" and "2020-05-11_00"
        * - {my_date:strftimedelta(60m,%Y-%m-%d_%H)}
          - [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 11, 6) ]
          - "2020-05-11_01" and "2020-05-11_07"
        * - {my_date:strftimedelta(7200s,%Y-%m-%d_%H)}
          - [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 11, 6) ]
          - "2020-05-11_02" and "2020-05-11_08"


Built-in pattern item functions
+++++++++++++++++++++++++++++++

The built-in pattern item functions are applied to the substituted values. The syntax is as follows::

    {param|function1|function2|...|functionN}

At the moment, the only built-in pattern function is ``lower``.

   .. list-table::
        :header-rows: 1
        :widths: auto

        * - Pattern
          - Value
          - Substituted value
        * - {param|lower}
          - ["T", "z", "Rhu" ]
          - "t", "z" and "rhu"
