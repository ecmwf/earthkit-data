Deprecations
=============


.. _deprecated-0.15.0:

Version 0.15.0
-----------------

.. _deprecated-ens-dim-role:

The "ens" dimension role has been renamed to "number"
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The name of the ensemble member :ref:`dimension role <_xr_dim_roles>` changed to "number" from "ens" in the ``dim_roles`` option of :py:meth:`~data.readers.grib.index.GribFieldList.to_xarray`. The old name is still available for backward compatibility but will be removed in a future release.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_ens_dim_role.py

   * - New code
   * -

        .. literalinclude:: include/migrated_ens_dim_role.py


.. _deprecated-xarray-accessor-to-grib:

The "to_grib" method on the earthkit Xarray accessor is deprecated
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The :func:`to_grib` method on the ``earthkit`` Xarray accessor is deprecated. Use :func:`to_target` instead. The method is still available for backward compatibility but will be removed in a future release. See :ref:`/examples/xarray_engine_to_grib.ipynb` notebook for details on how to use the new API.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_xarray_earthkit_to_grib.py

   * - New code
   * -

        .. literalinclude:: include/migrated_xarray_earthkit_to_grib.py



.. _deprecated-0.13.0:

Version 0.13.0
-----------------

.. _deprecated-settings:

The "settings" has been renamed to :ref:`config <config>`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The API did not change with the exception of ``settings.auto_save_settings``, which now is ``config.autosave``.
The "settings" object is still available for backward compatibility but will be removed in a future release.
Users are encouraged to migrate the code to use :ref:`config <config>` instead.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_settings.py

   * - New code
   * -

        .. literalinclude:: include/migrated_settings.py


.. _deprecated-auto-save-settings:

``settings.auto_save_settings`` is now ``config.autosave``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

See details :ref:`here <deprecated-settings>`.


.. _deprecated-data-save:

Data object :func:`save` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

This functionality is replaced by the :ref:`targets <data-targets>`.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_data_save.py

   * - New code
   * -

        .. literalinclude:: include/migrated_data_save.py


.. _deprecated-data-write:

Data object :func:`write` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

This functionality is now replaced by the :ref:`targets <data-targets>`.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

       .. literalinclude:: include/deprec_data_write.py

   * - New code
   * -

       .. literalinclude:: include/migrated_data_write.py



.. _deprecated-new-grib-output:

:func:`new_grib_output` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

:func:`new_grib_output` returns a new :py:class:`GribOutput` object. Its functionality is replaced by the :ref:`targets <data-targets>`.

.. warning::

    When using :func:`new_grib_output`, if the specified metadata does not contain the ``generatingProcessIdentifier`` key it is automatically set to ``255`` for the saved GRIB message. The new API does not have this behavior.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_new_grib_output.py

   * - New code
   * -

        .. literalinclude:: include/migrated_new_grib_output.py


The ``split_output=True`` option of  :func:`new_grib_output` is not supported by the :ref:`file <targets-file>` target but implemented by the :ref:`file-pattern <targets-file-pattern>` target.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_new_grib_output_split.py

   * - New code
   * -

        .. literalinclude:: include/migrated_new_grib_output_split.py


.. warning::

    When using :func:`new_grib_output` the ``{param}`` pattern substitutes the value of the ``"param"`` ecCodes key from the GRIB header. However, with the :ref:`targets <data-targets>` the ``{param}`` pattern substitutes the value of the ``"shortName"`` key. This is to match the behaviour of ``Field.metadata("param")``, which always returns the value of the ``"shortName"``. If you still want to use the value of the ``"param"`` ecCodes key you need to use the ``{mars.param}`` pattern instead.


    .. code-block:: python

        # Deprecated code
        new_grib_output("file", "output_{param}.grib", split_output=True)
        ...

        # New code
        to_target("file-pattern", "output_{mars.param}.grib")



.. _deprecated-griboutput:

:py:class:`GribOutput` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

Its functionality is replaced by the :ref:`targets <data-targets>` instead. For details see :ref:`migrating new_grib_output() <deprecated-new-grib-output>`.


.. _deprecated-new-grib-coder:

:func:`new_grib_coder` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

:func:`new_grib_coder` returns a new :py:class:`GribCoder` object. Its functionality is replaced by the :ref:`targets <data-targets>`.

.. warning::

    When using :func:`new_grib_coder`, if the specified metadata does not contain the ``generatingProcessIdentifier`` key it is automatically set to ``255`` in the generated GRIB message. The new API does not have this behavior.

.. list-table::
   :header-rows: 0

   * - Deprecated code
   * -

        .. literalinclude:: include/deprec_new_grib_coder.py


   * - New code
   * -

        .. literalinclude:: include/migrated_new_grib_coder.py


.. _deprecated-gribcoder:

:py:class:`GribCoder` is deprecated
++++++++++++++++++++++++++++++++++++++++++++

Its functionality is replaced by the :ref:`encoders <data-endoders>`. For details see :ref:`migrating new_grib_coder() <deprecated-new-grib-coder>`.
